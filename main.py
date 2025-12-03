import argparse
import json
import sys
import os

# ----------------------------------------------------
# Funções Principais
# ----------------------------------------------------

def load_config(config_path):
    """Carrega o arquivo JSON e retorna o dicionário de configurações."""
    if not os.path.exists(config_path):
        # Requisito 4: Tratamento de erro de arquivo não encontrado
        raise FileNotFoundError(f"Erro: O arquivo de configuração JSON não foi encontrado em '{config_path}'.")

    try:
        with open(config_path, 'r') as f:
            # Requisito 1: Fonte de parâmetros é um arquivo JSON
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        # Requisito 4: Tratamento de erro de sintaxe JSON
        raise ValueError(f"Erro: Falha ao analisar o arquivo JSON. Verifique a sintaxe.\nDetalhes: {e}")

def validate_config(config):
    """Valida se todos os parâmetros requeridos estão presentes e nos formatos esperados."""
    
    required_params = [
        'package_name',
        'repository_source',
        'repo_mode',
        'package_version',
        'output_mode_ascii_tree'
    ]
    
    # Requisito 4: Demonstração de tratamento de erros para todos os parâmetros
    
    # 1. Verificar a presença dos parâmetros
    for param in required_params:
        if param not in config:
            raise ValueError(f"Erro de Configuração: O parâmetro obrigatório '{param}' está faltando no arquivo JSON.")

    # 2. Verificar os tipos/valores dos parâmetros
    
    for param in ['package_name', 'repository_source', 'package_version']:
        if not isinstance(config[param], str) or not config[param].strip():
            raise TypeError(f"Erro de Configuração: '{param}' deve ser uma string não vazia.")

    # Validação de valor (repo_mode)
    valid_repo_modes = ['local', 'remote']
    if config['repo_mode'] not in valid_repo_modes:
        raise ValueError(f"Erro de Configuração: 'repo_mode' deve ser uma das seguintes opções: {valid_repo_modes}. Valor fornecido: {config['repo_mode']}")

    # Validação de tipo (output_mode_ascii_tree)
    if not isinstance(config['output_mode_ascii_tree'], bool):
        raise TypeError(f"Erro de Configuração: 'output_mode_ascii_tree' deve ser um booleano (true/false). Valor fornecido: {config['output_mode_ascii_tree']}")

    return config

def main():
    """Função principal que configura o CLI, carrega e exibe os parâmetros."""
    
    parser = argparse.ArgumentParser(
        description="CLI para visualização de grafos de dependência. Etapa 1: Carregar e exibir configurações JSON."
    )
    
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help="Caminho para o arquivo de configuração JSON."
    )

    args = parser.parse_args()
    
    print("--- Iniciando Etapa 1: Protocolo de Configuração JSON ---")

    try:
        # 1. Carregar configuração
        config_data = load_config(args.config)
        
        # 2. Validar configuração
        validated_config = validate_config(config_data)

        # Requisito 3: Exibir todos os parâmetros (chave-valor)
        print("\n✅ Configurações Carregadas e Validadas:")
        for key, value in validated_config.items():
            # Exibe chave: valor (tipo)
            print(f"- **{key}**: {value} (Tipo: {type(value).__name__})")
        
        print("\n--- Etapa 1 Concluída com Sucesso. ---")

    except Exception as e:
        # Requisito 4: Demonstração de tratamento de erros
        print(f"\n❌ ERRO FATAL na Configuração:")
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()