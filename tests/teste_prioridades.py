#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para validar as REGEX de ENVIO PRIORITÁRIO
"""

import re
import unicodedata

# ==============================================================================
# FUNÇÃO DE NORMALIZAÇÃO (IGUAL À DO ARQUIVO PRINCIPAL)
# ==============================================================================

def normalizar(txt: str) -> str:
    """
    Normaliza texto removendo acentos e convertendo para minúsculas.
    """
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    return txt.lower()

# ==============================================================================
# DICIONÁRIO DE PRIORIDADE (IGUAL AO DO ARQUIVO PRINCIPAL)
# ==============================================================================

DICIONARIO_DE_ENVIO_PRIORITARIO = {
    'Problemas SIAFERIO':
        r'\b(?:problema(?:s)?|erro(?:s)?|falha(?:s)?|indisponibilidade|instabilidade|lentidao)'
        r'(?:\s+(?:no|do|com|em))?\s+(?:siaferio|siafe[-\s]*rio|siaf[-\s]*e[-\s]*rio)\b'
        r'|\bsiaferio\s+(?:fora\s+do\s+ar|inoperante|com\s+problema(?:s)?|nao\s+(?:funciona|carrega|abre))\b',

    'Problemas SIAFEM':
        r'\b(?:problema(?:s)?|erro(?:s)?|falha(?:s)?|indisponibilidade|instabilidade|lentidao)'
        r'(?:\s+(?:no|do|com|em))?\s+(?:siafem|siaf[-\s]*em)\b'
        r'|\bsiafem\s+(?:fora\s+do\s+ar|inoperante|com\s+problema(?:s)?|nao\s+(?:funciona|carrega|abre))\b',

    'FlexVision':
        r'\bflexvision\b|\bflex[-\s]*vision\b',

    'Sistemas Fora do Ar':
        r'\b(?:sistema(?:s)?|servico(?:s)?|aplicacao(?:oes)?)\s+(?:fora\s+do\s+ar|indisponivel(?:eis)?|inoperante(?:s)?)\b'
        r'|\b(?:sem\s+acesso|nao\s+(?:acessa|conecta|funciona))\s+(?:ao\s+)?(?:sistema(?:s)?|siaferio|siafem)\b',

    'Urgente':
        r'\burgent(?:e|es?|issim[ao])\b|\bpriorit[aá]ri[ao](?:s)?\b|\bemerg[eê]ncia\b'
        r'|\basap\b|\bcom\s+urg[eê]ncia\b|\bpara\s+hoje\b|\bimediato\b',

    # 'Prazo Vencendo':
    #     r'\bprazo\s+(?:venc(?:e|endo|eu|ido)|expirado|esgotado)\b'
    #     r'|\b(?:ate|para)\s+(?:hoje|amanh[aã])\b'
    #     r'|\bfim\s+do\s+(?:dia|expediente|prazo)\b',

    'Erro Crítico':
        r'\b(?:erro\s+(?:critico|grave|fatal|sistema)|falha\s+(?:critica|grave|geral))\b'
        r'|\b(?:nao\s+(?:consegue|consigo)|impossivel)\s+(?:acessar|executar|processar|finalizar)\b'
        r'|\bsistema\s+(?:travado|congelado|nao\s+responde)\b',

    # 'Operacao Bloqueada':
    #     r'\b(?:bloqueado|impedido|impossibilitado)\s+de\s+(?:acessar|executar|processar)\b'
    #     r'|\bnao\s+(?:consegue|consigo)\s+(?:entrar|logar|acessar)\s+(?:no\s+)?(?:sistema(?:s)?|siaferio|siafem)\b'
    #     r'|\b(?:travado|parado|impedido)\s+(?:na|no)\s+(?:operacao|processo|sistema)\b',

    # 'Senha Bloqueada':
    #     r'\bsenha\s+(?:bloqueada|travada|expirada|vencida|invalidada)\b'
    #     r'|\b(?:usuario|login)\s+(?:bloqueado|inativo|suspenso)\b'
    #     r'|\bnao\s+(?:consegue|consigo)\s+(?:logar|fazer\s+login|entrar\s+no\s+sistema)\b',

    'Fechamento':
        r'\b(?:fechamento|encerramento)\s+(?:do\s+)?(?:mes|periodo|exercicio|balanco)\b'
        r'|\bfim\s+do\s+(?:mes|ano|exercicio|periodo)\b'
        r'|\b(?:prestacao|envio)\s+de\s+contas?\b',

    # 'Auditoria':
    #     r'\b(?:auditoria|fiscalizacao|inspecao|verificacao)\s+(?:tcm|tce|cgu|receita)\b'
    #     r'|\b(?:tcm|tce|cgu)\s+(?:solicitou|requisitou|pediu)\b'
    #     r'|\b(?:prestacao|envio)\s+de\s+contas\s+(?:ao\s+)?(?:tcm|tce)\b',
}

# ==============================================================================
# CASOS DE TESTE PARA PRIORIDADES
# ==============================================================================

casos_teste_prioridade = [
    # ── PROBLEMAS SIAFERIO ─────────────────────────────────────────────────────
    {
        "texto": "Problema no SIAFERIO, usuários não conseguem acessar.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFERIO"
    },
    {
        "texto": "SIAFERIO está com erro crítico desde manhã.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFERIO"
    },
    {
        "texto": "Sistema SIAFe-RIO fora do ar há 2 horas.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFERIO"
    },
    {
        "texto": "Falha no SIAFE-Rio, precisa verificar urgente.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFERIO"
    },
    {
        "texto": "SIAFERIO não funciona desde ontem.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFERIO"
    },
    
    # ── PROBLEMAS SIAFEM ───────────────────────────────────────────────────────
    {
        "texto": "Erro no SIAFEM, sistema não carrega.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFEM"
    },
    {
        "texto": "SIAFEM inoperante desde esta manhã.",
        "deve_priorizar": True,
        "conceito_esperado": "Problemas SIAFEM"
    },
    
    # ── FLEXVISION ─────────────────────────────────────────────────────────────
    {
        "texto": "FlexVision apresentando inconsistências.",
        "deve_priorizar": True,
        "conceito_esperado": "FlexVision"
    },
    {
        "texto": "Problema no Flex-Vision, precisa correção.",
        "deve_priorizar": True,
        "conceito_esperado": "FlexVision"
    },
    
    # ── URGÊNCIAS ──────────────────────────────────────────────────────────────
    {
        "texto": "URGENTE: Precisa resolver até hoje.",
        "deve_priorizar": True,
        "conceito_esperado": "Urgente"
    },
    {
        "texto": "Assunto prioritário para amanhã.",
        "deve_priorizar": True,
        "conceito_esperado": "Urgente"
    },
    {
        "texto": "EMERGÊNCIA no processamento dos dados.",
        "deve_priorizar": True,
        "conceito_esperado": "Urgente"
    },
    {
        "texto": "Preciso ASAP da liberação do sistema.",
        "deve_priorizar": True,
        "conceito_esperado": "Urgente"
    },
    
    # ── PRAZOS ─────────────────────────────────────────────────────────────────
    {
        "texto": "Prazo vencendo hoje às 18h.",
        "deve_priorizar": True,
        "conceito_esperado": "Prazo Vencendo"
    },
    {
        "texto": "Até amanhã precisa estar finalizado.",
        "deve_priorizar": True,
        "conceito_esperado": "Prazo Vencendo"
    },
    {
        "texto": "Fim do expediente é o prazo limite.",
        "deve_priorizar": True,
        "conceito_esperado": "Prazo Vencendo"
    },
    
    # ── OPERAÇÕES BLOQUEADAS ───────────────────────────────────────────────────
    {
        "texto": "Não consigo entrar no sistema SIAFERIO.",
        "deve_priorizar": True,
        "conceito_esperado": "Operacao Bloqueada"
    },
    {
        "texto": "Usuário bloqueado de acessar a funcionalidade.",
        "deve_priorizar": True,
        "conceito_esperado": "Operacao Bloqueada"
    },
    {
        "texto": "Sistema travado na operação de cadastro.",
        "deve_priorizar": True,
        "conceito_esperado": "Operacao Bloqueada"
    },
    
    # ── SENHAS E LOGIN ─────────────────────────────────────────────────────────
    {
        "texto": "Senha bloqueada no sistema, preciso reativar.",
        "deve_priorizar": True,
        "conceito_esperado": "Senha Bloqueada"
    },
    {
        "texto": "Não consegue fazer login no SIAFEM.",
        "deve_priorizar": True,
        "conceito_esperado": "Senha Bloqueada"
    },
    {
        "texto": "Usuário inativo, precisa reativação urgente.",
        "deve_priorizar": True,
        "conceito_esperado": "Senha Bloqueada"
    },
    
    # ── FECHAMENTOS ────────────────────────────────────────────────────────────
    {
        "texto": "Fechamento do mês em andamento.",
        "deve_priorizar": True,
        "conceito_esperado": "Fechamento"
    },
    {
        "texto": "Prestação de contas deve ser enviada hoje.",
        "deve_priorizar": True,
        "conceito_esperado": "Fechamento"
    },
    
    # ── AUDITORIA ──────────────────────────────────────────────────────────────
    {
        "texto": "TCM solicitou informações urgentes.",
        "deve_priorizar": True,
        "conceito_esperado": "Auditoria"
    },
    {
        "texto": "Auditoria do TCE precisa dos dados até amanhã.",
        "deve_priorizar": True,
        "conceito_esperado": "Auditoria"
    },
    
    # ── CASOS QUE NÃO DEVEM SER PRIORIZADOS ───────────────────────────────────
    {
        "texto": "Reunião sobre novos procedimentos na próxima semana.",
        "deve_priorizar": False,
        "conceito_esperado": None
    },
    {
        "texto": "Cadastro de novo fornecedor pode ser feito quando possível.",
        "deve_priorizar": False,
        "conceito_esperado": None
    },
    {
        "texto": "Informações sobre cursos e treinamentos disponíveis.",
        "deve_priorizar": False,
        "conceito_esperado": None
    },
]

# ==============================================================================
# FUNÇÃO DE TESTE
# ==============================================================================

def testar_prioridades():
    """
    Executa todos os casos de teste de prioridade e mostra os resultados.
    """
    print("=== TESTE DE VALIDAÇÃO DAS REGEX DE ENVIO PRIORITÁRIO ===\n")
    
    acertos = 0
    total = len(casos_teste_prioridade)
    
    for i, caso in enumerate(casos_teste_prioridade, 1):
        texto_original = caso["texto"]
        deve_priorizar = caso["deve_priorizar"]
        conceito_esperado = caso["conceito_esperado"]
        
        # Normalizar o texto
        texto_normalizado = normalizar(texto_original)
        
        # Testar contra o dicionário de prioridades
        encontrou_prioridade = False
        conceito_encontrado = ""
        trecho_casado = ""
        
        for conceito, padrao in DICIONARIO_DE_ENVIO_PRIORITARIO.items():
            match = re.search(padrao, texto_normalizado, flags=re.IGNORECASE|re.DOTALL)
            if match:
                encontrou_prioridade = True
                conceito_encontrado = conceito
                trecho_casado = match.group(0)
                break
        
        # Verificar resultado
        resultado_correto = (encontrou_prioridade == deve_priorizar)
        if resultado_correto and (not deve_priorizar or conceito_encontrado == conceito_esperado):
            status = "✅ PASSOU"
            acertos += 1
        else:
            status = "❌ FALHOU"
        
        print(f"Teste {i:2d}: {status}")
        print(f"  Texto: \"{texto_original}\"")
        print(f"  Esperado: {'PRIORIZAR' if deve_priorizar else 'NÃO PRIORIZAR'}")
        print(f"  Resultado: {'PRIORIZOU' if encontrou_prioridade else 'NÃO PRIORIZOU'}")
        
        if encontrou_prioridade:
            print(f"  Conceito: {conceito_encontrado}")
            print(f"  Trecho encontrado: \"{trecho_casado}\"")
        
        if not resultado_correto:
            print(f"  ⚠️  Conceito esperado: {conceito_esperado}")
        
        print()
    
    print("=" * 60)
    print(f"RESULTADO FINAL: {acertos}/{total} testes passaram ({acertos/total*100:.1f}%)")
    
    if acertos == total:
        print("🎉 Todos os testes passaram! As regex de prioridade estão funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Revise os padrões que não passaram.")

# ==============================================================================
# EXECUÇÃO DO TESTE
# ==============================================================================

if __name__ == "__main__":
    testar_prioridades()