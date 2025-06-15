#!/usr/bin/env python
"""
run_tests.py - Script simplificado para ejecutar tests
Uso: python run_tests.py [simple|all|coverage]
"""
import os
import sys
import subprocess


def main():
    """Función principal"""
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("manage.py"):
        print(
            "❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto (donde está manage.py)"
        )
        sys.exit(1)

    # Determinar comando
    command = sys.argv[1] if len(sys.argv) > 1 else "simple"

    if command == "simple":
        print("🧪 Ejecutando tests simplificados...")
        result = subprocess.run(
            [
                sys.executable,
                "manage.py",
                "test",
                "guessityet.test_simple",
                "--verbosity=2",
            ]
        )

    elif command == "all":
        print("🧪 Ejecutando todos los tests...")
        result = subprocess.run(
            [sys.executable, "manage.py", "test", "guessityet", "--verbosity=2"]
        )

    elif command == "coverage":
        print("🧪 Ejecutando tests con coverage...")
        try:
            # Ejecutar tests con coverage
            result = subprocess.run(
                [
                    "coverage",
                    "run",
                    "--source=guessityet",
                    "manage.py",
                    "test",
                    "guessityet.test_simple",
                ]
            )

            if result.returncode == 0:
                print("\n📊 Generando reporte de coverage...")
                subprocess.run(["coverage", "report", "-m"])
                subprocess.run(["coverage", "html"])
                print("📄 Reporte HTML generado en htmlcov/index.html")

        except FileNotFoundError:
            print("⚠️ Coverage no instalado. Ejecutando tests sin coverage...")
            result = subprocess.run(
                [
                    sys.executable,
                    "manage.py",
                    "test",
                    "guessityet.test_simple",
                    "--verbosity=2",
                ]
            )

    else:
        print(f"Comando desconocido: {command}")
        print("Uso: python run_tests.py [simple|all|coverage]")
        print("  simple   - Ejecutar tests básicos (por defecto)")
        print("  all      - Ejecutar todos los tests")
        print("  coverage - Ejecutar con reporte de coverage")
        sys.exit(1)

    # Verificar resultado
    if result.returncode == 0:
        print("\n✅ Tests completados exitosamente!")
    else:
        print(f"\n❌ Tests fallaron (código: {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
