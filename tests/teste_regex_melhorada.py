#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste unitário para validar as melhorias de REGEX implementadas
na automação de comunicas.
"""

import re
import unicodedata

# ==============================================================================
# FUNÇÃO DE NORMALIZAÇÃO (IGUAL À DO ARQUIVO PRINCIPAL)
# ==============================================================================

def normalizar(txt: str) -> str:
    """
    Normaliza texto removendo acentos e convertendo para minúsculas.
    Isso torna as regex mais simples e robustas.
    """
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")  # remove acentos
    return txt.lower()

# ==============================================================================
# PADRÕES AUXILIARES (IGUAIS AOS DO ARQUIVO PRINCIPAL)
# ==============================================================================

PREP = r'(?:de|do|da|dos|das|no|na|nos|nas)'
PT_OBJ = r'programa(?:s)?\s*(?:de|-)?\s*trabalho(?:s)?'
ACOES = r'(?:cadastr(?:o(?:s)?|ar|ado(?:s)?|amento|ou)|libera(?:cao|r|do(?:s)?)|inativa(?:cao|r|do(?:s)?))'

# ==============================================================================
# DICIONÁRIO DE TESTE (IGUAL AO DO ARQUIVO PRINCIPAL)
# ==============================================================================

DICIONARIO_DE_BLOQUEIO_REGEX = {
    'Inscricao Generica':
        r'\binscri(?:cao|coes)\s+generica(?:s)?\b',

    'Credor Generico':
        r'\bcredor(?:es)?\s+generic(?:o|os)\b|\bcgs\b',

    'Bloqueio Judicial':
        r'\bbloqueio(?:s)?\s+judicia(?:l|is)\b|\bcriaca(?:o|oes)\s+de\s+bj\b|\bbj\b',

    'Codigo de Barras':
        r'\b(?:cod(?:\.|\s*)barras?|codigo(?:s)?\s+de\s+barras?)\b'
        r'|\balterac(?:ao|oes)\s+de\s+cnpj\s+em\s+(?:cod(?:\.|\s*)barras?|codigo\s+de\s+barras?)\b',

    'Programa de Trabalho':
        r'\b(?:'
        rf'(?:{ACOES}(?:\s+(?:o|a|os|as))?\s*(?:\s+no\s+sistema)?(?:\s+{PREP})?\s+{PT_OBJ})'
        r'|'
        rf'(?:{PT_OBJ}(?:\s+no\s+sistema)?(?:\s+(?:foi|foram|esta(?:o)?|sera(?:o)?))?\s*(?:\w+\s+){{0,6}}{ACOES})'
        r')\b',

    'Acesso ou Senha':
        r'(?:(?:\bacesso(?:s)?\b|\bsenha(?:s)?\b).{0,25}\b(?:siafem|siaferio)\b|\bsiafem\b|\bsiaferio\b)',
}

# ==============================================================================
# CASOS DE TESTE
# ==============================================================================

casos_teste = [
    # Casos que DEVEM ser bloqueados
    {
        "texto": "Solicito inscrição genérica para o fornecedor XYZ.",
        "deve_bloquear": True,
        "conceito_esperado": "Inscricao Generica"
    },
    {
        "texto": "Favor criar CGS para o novo credor.",
        "deve_bloquear": True,
        "conceito_esperado": "Credor Generico"
    },
    {
        "texto": "Necessário BJ para bloqueio de valores.",
        "deve_bloquear": True,
        "conceito_esperado": "Bloqueio Judicial"
    },
    {
        "texto": "Alterar código de barras do documento.",
        "deve_bloquear": True,
        "conceito_esperado": "Codigo de Barras"
    },
    {
        "texto": "Programa de trabalho foi cadastrado no sistema ontem.",
        "deve_bloquear": True,
        "conceito_esperado": "Programa de Trabalho"
    },
    {
        "texto": "Cadastrar o programa de trabalho no sistema.",
        "deve_bloquear": True,
        "conceito_esperado": "Programa de Trabalho"
    },
    {
        "texto": "Preciso do acesso ao SIAFEM urgente.",
        "deve_bloquear": True,
        "conceito_esperado": "Acesso ou Senha"
    },
    {
        "texto": "Senha do SIAFERIO foi esquecida.",
        "deve_bloquear": True,
        "conceito_esperado": "Acesso ou Senha"
    },
    
    # Casos que NÃO devem ser bloqueados (falsos positivos)
    {
        "texto": "O programa específico não precisa de trabalho adicional.",
        "deve_bloquear": False,
        "conceito_esperado": None
    },
    {
        "texto": "Reunião sobre programas governamentais de educação.",
        "deve_bloquear": False,
        "conceito_esperado": None
    },
    {
        "texto": "Relatório de despesas diversas do setor.",
        "deve_bloquear": False,
        "conceito_esperado": None
    },
    
    # Casos com acentos e variações (teste de normalização)
    {
        "texto": "Inscrição genérica necessária para fornecedor.",
        "deve_bloquear": True,
        "conceito_esperado": "Inscricao Generica"
    },
    {
        "texto": "Bloqueio judicial está pendente de análise.",
        "deve_bloquear": True,
        "conceito_esperado": "Bloqueio Judicial"
    },
]

# ==============================================================================
# FUNÇÃO DE TESTE
# ==============================================================================

def testar_regex():
    """
    Executa todos os casos de teste e mostra os resultados.
    """
    print("=== TESTE DE VALIDAÇÃO DAS REGEX MELHORADAS ===\n")
    
    acertos = 0
    total = len(casos_teste)
    
    for i, caso in enumerate(casos_teste, 1):
        texto_original = caso["texto"]
        deve_bloquear = caso["deve_bloquear"]
        conceito_esperado = caso["conceito_esperado"]
        
        # Normalizar o texto (como na automação)
        texto_normalizado = normalizar(texto_original)
        
        # Testar contra o dicionário
        encontrou_bloqueio = False
        conceito_encontrado = ""
        trecho_casado = ""
        
        for conceito, padrao in DICIONARIO_DE_BLOQUEIO_REGEX.items():
            match = re.search(padrao, texto_normalizado, flags=re.IGNORECASE|re.DOTALL)
            if match:
                encontrou_bloqueio = True
                conceito_encontrado = conceito
                trecho_casado = match.group(0)
                break
        
        # Verificar resultado
        resultado_correto = (encontrou_bloqueio == deve_bloquear)
        if resultado_correto and (not deve_bloquear or conceito_encontrado == conceito_esperado):
            status = "✅ PASSOU"
            acertos += 1
        else:
            status = "❌ FALHOU"
        
        print(f"Teste {i:2d}: {status}")
        print(f"  Texto: \"{texto_original}\"")
        print(f"  Esperado: {'BLOQUEAR' if deve_bloquear else 'PERMITIR'}")
        print(f"  Resultado: {'BLOQUEOU' if encontrou_bloqueio else 'PERMITIU'}")
        
        if encontrou_bloqueio:
            print(f"  Conceito: {conceito_encontrado}")
            print(f"  Trecho encontrado: \"{trecho_casado}\"")
        
        if not resultado_correto:
            print(f"  ⚠️  Conceito esperado: {conceito_esperado}")
        
        print()
    
    print("=" * 50)
    print(f"RESULTADO FINAL: {acertos}/{total} testes passaram ({acertos/total*100:.1f}%)")
    
    if acertos == total:
        print("🎉 Todos os testes passaram! As regex estão funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Revise os padrões que não passaram.")

# ==============================================================================
# EXECUÇÃO DO TESTE
# ==============================================================================

if __name__ == "__main__":
    testar_regex()