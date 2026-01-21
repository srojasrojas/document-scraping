"""
Módulo para convertir archivos PPTX a PDF con múltiples backends.

Soporta:
- LibreOffice (multiplataforma, gratis)
- PowerPoint COM (Windows, requiere PowerPoint instalado)

Uso:
    from pptx_converter import convert_pptx_to_pdf
    
    pdf_path = convert_pptx_to_pdf("presentation.pptx")
    print(f"PDF generado: {pdf_path}")
"""

import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, Literal
import json


class PPTXConverter:
    """Convierte archivos PPTX a PDF usando diferentes backends"""
    
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
            self.config = config.get('extraction', {}).get('pptx_conversion', {})
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.config = {}
        
        # Configuración por defecto
        self.enabled = self.config.get('enabled', True)
        preferred_backend = self.config.get('backend', 'auto')
        self.delete_temp_pdf = self.config.get('delete_temp_pdf', False)
        self.temp_dir = self.config.get('temp_dir', 'output/temp_pdfs')
        self.dpi = self.config.get('dpi', 300)
        
        # Detectar backend disponible
        self.backend = self._detect_backend() if preferred_backend == "auto" else preferred_backend
        
        if not self.enabled:
            print("⚠️  Conversión PPTX deshabilitada en configuración")
        else:
            print(f"✓ Conversor PPTX inicializado: {self.backend}")
    
    def _detect_backend(self) -> str:
        """
        Detecta automáticamente el mejor backend disponible
        
        Returns:
            Nombre del backend: "powerpoint" o "libreoffice"
        
        Raises:
            RuntimeError: Si no se encuentra ningún backend
        """
        # En Windows, intentar PowerPoint primero (mejor calidad)
        if platform.system() == "Windows":
            if self._check_powerpoint():
                return "powerpoint"
        
        # Fallback a LibreOffice (multiplataforma)
        if self._check_libreoffice():
            return "libreoffice"
        
        raise RuntimeError(
            "❌ No se encontró ningún backend de conversión PPTX→PDF.\n"
            "   Instala una de estas opciones:\n"
            "   1. LibreOffice (recomendado, multiplataforma):\n"
            "      Windows: choco install libreoffice\n"
            "      macOS:   brew install --cask libreoffice\n"
            "      Linux:   sudo apt-get install libreoffice\n"
            "   2. Microsoft PowerPoint (solo Windows, máxima calidad)\n"
        )
    
    def _check_powerpoint(self) -> bool:
        """
        Verifica si PowerPoint está disponible via COM (Windows)
        
        Returns:
            True si PowerPoint está instalado y accesible
        """
        if platform.system() != "Windows":
            return False
        
        try:
            import comtypes.client
            # Intentar crear objeto PowerPoint
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Quit()
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
    
    def convert(self, pptx_path: str, output_dir: Optional[str] = None) -> str:
        """
        Convierte un archivo PPTX a PDF
        
        Args:
            pptx_path: Ruta al archivo PPTX
            output_dir: Directorio de salida (default: mismo que PPTX)
        
        Returns:
            Ruta al archivo PDF generado
        
        Raises:
            FileNotFoundError: Si el archivo PPTX no existe
            RuntimeError: Si la conversión falla
        """
        pptx_file = Path(pptx_path)
        if not pptx_file.exists():
            raise FileNotFoundError(f"No se encontró: {pptx_path}")
        
        # Determinar directorio de salida
        if output_dir is None:
            output_dir = pptx_file.parent
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir / f"{pptx_file.stem}.pdf"
        
        # Realizar conversión según backend
        try:
            if self.backend == "libreoffice":
                self._convert_libreoffice(pptx_file, output_dir)
            elif self.backend == "powerpoint":
                self._convert_powerpoint(pptx_file, pdf_path)
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
    
    def _convert_libreoffice(self, pptx_file: Path, output_dir: Path):
        """
        Convierte usando LibreOffice en modo headless
        
        Args:
            pptx_file: Path al archivo PPTX
            output_dir: Path al directorio de salida
        
        Raises:
            RuntimeError: Si LibreOffice falla
        """
        print(f"  → Convirtiendo con LibreOffice: {pptx_file.name}")
        
        cmd = [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(pptx_file.absolute())
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
    
    def _convert_powerpoint(self, pptx_file: Path, pdf_path: Path):
        """
        Convierte usando PowerPoint COM (Windows)
        
        Args:
            pptx_file: Path al archivo PPTX
            pdf_path: Path al PDF de salida
        
        Raises:
            RuntimeError: Si PowerPoint falla
        """
        print(f"  → Convirtiendo con PowerPoint COM: {pptx_file.name}")
        
        try:
            import comtypes.client
        except ImportError:
            raise RuntimeError(
                "Módulo 'comtypes' no instalado.\n"
                "Instala con: pip install comtypes"
            )
        
        powerpoint = None
        deck = None
        
        try:
            # Crear aplicación PowerPoint
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = 1  # 0 = invisible, 1 = visible
            
            # Abrir presentación
            deck = powerpoint.Presentations.Open(
                str(pptx_file.absolute()),
                ReadOnly=True,
                WithWindow=False
            )
            
            # Guardar como PDF (32 = ppSaveAsPDF)
            deck.SaveAs(str(pdf_path.absolute()), 32)
            
            print(f"     ✓ PDF generado con PowerPoint")
            
        except Exception as e:
            raise RuntimeError(f"Error en PowerPoint COM: {e}")
        
        finally:
            # Cerrar recursos
            if deck:
                try:
                    deck.Close()
                except:
                    pass
            if powerpoint:
                try:
                    powerpoint.Quit()
                except:
                    pass


def convert_pptx_to_pdf(pptx_path: str, 
                        output_dir: Optional[str] = None,
                        config_path: str = "config.json") -> str:
    """
    Función de conveniencia para convertir PPTX a PDF
    
    Args:
        pptx_path: Ruta al archivo PPTX
        output_dir: Directorio de salida opcional
        config_path: Ruta al archivo de configuración
    
    Returns:
        Ruta al archivo PDF generado
    
    Example:
        >>> pdf_path = convert_pptx_to_pdf("presentation.pptx")
        >>> print(f"Convertido a: {pdf_path}")
    """
    converter = PPTXConverter(config_path)
    return converter.convert(pptx_path, output_dir)


if __name__ == "__main__":
    # Test del conversor
    import sys
    
    print("=== Test del Conversor PPTX → PDF ===\n")
    
    if len(sys.argv) > 1:
        # Test con archivo provisto
        pptx_file = sys.argv[1]
        try:
            print(f"Convirtiendo: {pptx_file}\n")
            pdf_path = convert_pptx_to_pdf(pptx_file)
            print(f"\n✓ Éxito! PDF generado: {pdf_path}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        # Solo verificar backends disponibles
        try:
            converter = PPTXConverter()
            print(f"\n✓ Backend detectado: {converter.backend}")
            print("\nUso: python pptx_converter.py <archivo.pptx>")
        except RuntimeError as e:
            print(f"\n{e}")
            sys.exit(1)
