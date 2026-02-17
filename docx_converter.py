"""
Módulo para convertir archivos DOCX a PDF con múltiples backends.

Soporta:
- LibreOffice (multiplataforma, gratis)
- Word COM (Windows, requiere Word instalado)

Uso:
    from docx_converter import convert_docx_to_pdf
    
    pdf_path = convert_docx_to_pdf("document.docx")
    print(f"PDF generado: {pdf_path}")
"""

import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional
import json


class DOCXConverter:
    """Convierte archivos DOCX a PDF usando diferentes backends"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el conversor con configuración opcional
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        # Cargar configuración
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.config = config.get('extraction', {}).get('docx_conversion', {})
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.config = {}
        
        # Configuración por defecto
        self.enabled = self.config.get('enabled', True)
        preferred_backend = self.config.get('backend', 'auto')
        self.delete_temp_pdf = self.config.get('delete_temp_pdf', False)
        self.temp_dir = self.config.get('temp_dir', 'output/temp_pdfs')
        
        # Detectar backend disponible
        self.backend = self._detect_backend() if preferred_backend == "auto" else preferred_backend
        
        if not self.enabled:
            print("⚠️  Conversión DOCX deshabilitada en configuración")
        else:
            print(f"✓ Conversor DOCX inicializado: {self.backend}")
    
    def _detect_backend(self) -> str:
        """
        Detecta automáticamente el mejor backend disponible
        
        Returns:
            Nombre del backend: "word" o "libreoffice"
        
        Raises:
            RuntimeError: Si no se encuentra ningún backend
        """
        # En Windows, intentar Word primero (mejor calidad)
        if platform.system() == "Windows":
            if self._check_word():
                return "word"
        
        # Fallback a LibreOffice (multiplataforma)
        if self._check_libreoffice():
            return "libreoffice"
        
        raise RuntimeError(
            "❌ No se encontró ningún backend de conversión DOCX→PDF.\n"
            "   Instala una de estas opciones:\n"
            "   1. LibreOffice (recomendado, multiplataforma):\n"
            "      Windows: choco install libreoffice\n"
            "      macOS:   brew install --cask libreoffice\n"
            "      Linux:   sudo apt-get install libreoffice\n"
            "   2. Microsoft Word (solo Windows, máxima calidad)\n"
        )
    
    def _check_word(self) -> bool:
        """
        Verifica si Word está disponible via COM (Windows)
        
        Returns:
            True si Word está instalado y accesible
        """
        if platform.system() != "Windows":
            return False
        
        try:
            import comtypes.client
            # Intentar crear objeto Word
            word = comtypes.client.CreateObject("Word.Application")
            word.Quit()
            return True
        except Exception:
            return False
    
    def _check_libreoffice(self) -> bool:
        """
        Verifica si LibreOffice está instalado
        
        Returns:
            True si soffice está en PATH
        """
        return shutil.which("soffice") is not None
    
    def convert(self, docx_path: str, output_dir: Optional[str] = None) -> str:
        """
        Convierte un archivo DOCX a PDF
        
        Args:
            docx_path: Ruta al archivo DOCX
            output_dir: Directorio de salida (default: mismo que DOCX)
        
        Returns:
            Ruta al archivo PDF generado
        
        Raises:
            FileNotFoundError: Si el archivo DOCX no existe
            RuntimeError: Si la conversión falla
        """
        docx_file = Path(docx_path)
        if not docx_file.exists():
            raise FileNotFoundError(f"No se encontró: {docx_path}")
        
        # Determinar directorio de salida
        if output_dir is None:
            output_dir = docx_file.parent
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir / f"{docx_file.stem}.pdf"
        
        # Realizar conversión según backend
        try:
            if self.backend == "libreoffice":
                self._convert_libreoffice(docx_file, output_dir)
            elif self.backend == "word":
                self._convert_word(docx_file, pdf_path)
            else:
                raise RuntimeError(f"Backend desconocido: {self.backend}")
        except Exception as e:
            raise RuntimeError(f"Error en conversión con {self.backend}: {e}")
        
        # Verificar que el PDF fue creado
        if not pdf_path.exists():
            raise RuntimeError(
                f"La conversión no generó el archivo esperado: {pdf_path}\n"
                f"Backend usado: {self.backend}"
            )
        
        # Verificar que tiene contenido
        if pdf_path.stat().st_size == 0:
            raise RuntimeError(f"El PDF generado está vacío: {pdf_path}")
        
        return str(pdf_path)
    
    def _convert_libreoffice(self, docx_file: Path, output_dir: Path):
        """
        Convierte usando LibreOffice en modo headless
        
        Args:
            docx_file: Path al archivo DOCX
            output_dir: Path al directorio de salida
        
        Raises:
            RuntimeError: Si LibreOffice falla
        """
        print(f"  → Convirtiendo con LibreOffice: {docx_file.name}")
        
        cmd = [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(docx_file.absolute())
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos máximo
                check=False
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Error desconocido"
                raise RuntimeError(f"LibreOffice retornó código {result.returncode}: {error_msg}")
            
            print(f"     ✓ PDF generado exitosamente")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("LibreOffice excedió el tiempo límite (120s)")
        except FileNotFoundError:
            raise RuntimeError(
                "No se encontró 'soffice'. ¿LibreOffice está instalado?\n"
                "Instala con: choco install libreoffice"
            )
    
    def _convert_word(self, docx_file: Path, pdf_path: Path):
        """
        Convierte usando Word COM (Windows)
        
        Args:
            docx_file: Path al archivo DOCX
            pdf_path: Path al PDF de salida
        
        Raises:
            RuntimeError: Si Word falla
        """
        print(f"  → Convirtiendo con Word COM: {docx_file.name}")
        
        try:
            import comtypes.client
        except ImportError:
            raise RuntimeError(
                "Módulo 'comtypes' no instalado.\n"
                "Instala con: pip install comtypes"
            )
        
        word = None
        doc = None
        
        try:
            # Crear aplicación Word
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            
            # Abrir documento
            doc = word.Documents.Open(str(docx_file.absolute()))
            
            # Guardar como PDF (17 = wdFormatPDF)
            doc.SaveAs(str(pdf_path.absolute()), FileFormat=17)
            
            print(f"     ✓ PDF generado con Word")
            
        except Exception as e:
            raise RuntimeError(f"Error en Word COM: {e}")
        
        finally:
            # Cerrar recursos
            if doc:
                try:
                    doc.Close()
                except:
                    pass
            if word:
                try:
                    word.Quit()
                except:
                    pass


def convert_docx_to_pdf(docx_path: str, 
                        output_dir: Optional[str] = None,
                        config_path: str = "config.json") -> str:
    """
    Función de conveniencia para convertir DOCX a PDF
    
    Args:
        docx_path: Ruta al archivo DOCX
        output_dir: Directorio de salida opcional
        config_path: Ruta al archivo de configuración
    
    Returns:
        Ruta al archivo PDF generado
    
    Example:
        >>> pdf_path = convert_docx_to_pdf("document.docx")
        >>> print(f"Convertido a: {pdf_path}")
    """
    converter = DOCXConverter(config_path)
    return converter.convert(docx_path, output_dir)


if __name__ == "__main__":
    # Test del conversor
    import sys
    
    print("=== Test del Conversor DOCX → PDF ===\n")
    
    if len(sys.argv) > 1:
        # Test con archivo provisto
        docx_file = sys.argv[1]
        try:
            print(f"Convirtiendo: {docx_file}\n")
            pdf_path = convert_docx_to_pdf(docx_file)
            print(f"\n✓ Éxito! PDF generado: {pdf_path}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        # Solo verificar backends disponibles
        try:
            converter = DOCXConverter()
            print(f"\n✓ Backend detectado: {converter.backend}")
            print("\nUso: python docx_converter.py <archivo.docx>")
        except RuntimeError as e:
            print(f"\n{e}")
            sys.exit(1)
