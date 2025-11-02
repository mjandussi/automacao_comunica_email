#!/usr/bin/env python3
"""
Script para validar o encoding do requirements.txt
Usado para garantir que o arquivo está em UTF-8 puro, sem BOM ou caracteres especiais
"""

import sys

def validate_requirements():
    """Valida se o requirements.txt está em UTF-8 correto"""
    try:
        with open('requirements.txt', 'rb') as f:
            content = f.read()

        # Verificar se tem BOM UTF-16
        if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
            print("[ERRO] requirements.txt está em UTF-16!")
            print("       Deve ser convertido para UTF-8")
            return False

        # Verificar se tem caracteres nulos (típico de UTF-16)
        if b'\x00' in content:
            print("[ERRO] requirements.txt contém caracteres nulos (provável UTF-16)!")
            print("       Deve ser convertido para UTF-8")
            return False

        # Tentar decodificar como UTF-8
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"[ERRO] requirements.txt não pode ser decodificado como UTF-8: {e}")
            return False

        # Validar que cada linha tem o formato correto
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        for i, line in enumerate(lines, 1):
            if '==' not in line:
                print(f"[AVISO] Linha {i} não tem formato esperado (package==version): {line}")

        print(f"[OK] requirements.txt está válido!")
        print(f"     - Encoding: UTF-8")
        print(f"     - Linhas: {len(lines)}")
        print(f"     - Tamanho: {len(content)} bytes")
        return True

    except FileNotFoundError:
        print("[ERRO] requirements.txt não encontrado!")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    success = validate_requirements()
    sys.exit(0 if success else 1)
