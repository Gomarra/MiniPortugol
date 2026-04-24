# analise_sintatica.py
import logging
import subprocess
from antlr4 import CommonTokenStream
from miniportugolParser import miniportugolParser # Arquivo gerado pelo ANTLR
from erro import Erro, CustomErrorListener # Do nosso arquivo erro.py

class AnaliseSintatica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ast = None

    def executarAnaliseSintatica(self, token_stream: CommonTokenStream):
        self.logger.info("Iniciando análise sintática...")
        if not token_stream:
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, "Stream de tokens não fornecida.", tipo_erro="SINTATICO")
            return None
        try:
            parser = miniportugolParser(token_stream)
            parser.removeErrorListeners()
            parser.addErrorListener(CustomErrorListener(self.erro_handler, "Analisador Sintático"))

            self.ast = parser.program()

            if not self.erro_handler.tem_erros_sintaticos:
                self.logger.info("Análise sintática concluída com sucesso. AST gerada.")
            else:
                self.logger.error("Análise sintática encontrou erros. AST pode estar incompleta ou incorreta.")
            return self.ast
        except Exception as e:
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, f"Erro inesperado na análise sintática: {e}", tipo_erro="SINTATICO")
            return None

    def _gerar_dot_recursivo(self, no, parser_rules, id_map, dot_linhas):
        no_id = id(no)
        if no_id not in id_map:
            id_map[no_id] = len(id_map)

        # Determina o label do nó
        if hasattr(no, 'getRuleIndex'): # É um nó de regra
            label = parser_rules[no.getRuleIndex()]
        elif hasattr(no, 'symbol'): # É um nó terminal (token)
            texto_escapado = no.getText().replace('"', '\\"')
            token_name = miniportugolParser.symbolicNames[no.symbol.type]
            label = f"{texto_escapado}\\n<Token: {token_name}>"
        else: # Outro tipo de nó (ex: ErrorNode)
            label = str(no.getText()).replace('"', '\\"')

        dot_linhas.append(f'  node{id_map[no_id]} [label="{label}"];')

        if hasattr(no, 'children') and no.children:
            for child in no.children:
                child_id = id(child)
                if child_id not in id_map:
                    id_map[child_id] = len(id_map)
                dot_linhas.append(f'  node{id_map[no_id]} -- node{id_map[child_id]};')
                self._gerar_dot_recursivo(child, parser_rules, id_map, dot_linhas)

    def exportarAST_DOT(self, ast, nome_arquivo_dot: str):
        self.logger.info(f"Exportando AST para o formato DOT: {nome_arquivo_dot}")
        if not ast or self.erro_handler.tem_erros_sintaticos: # Não exportar se AST é nula ou houve erro sintático
            self.logger.warning("AST não disponível ou inválida para exportação DOT.")
            return

        try:
            parser_temp = miniportugolParser(None)
            parser_rules = parser_temp.ruleNames

            dot_linhas = ['graph BASIQuinhoAST {', '  node [fontname="Arial" shape=box];', '  edge [arrowhead=none];']
            id_map = {}
            self._gerar_dot_recursivo(ast, parser_rules, id_map, dot_linhas)
            dot_linhas.append('}')

            with open(nome_arquivo_dot, 'w', encoding='utf-8') as f:
                f.write('\n'.join(dot_linhas))
            self.logger.info(f"AST exportada com sucesso para {nome_arquivo_dot}")
        except Exception as e:
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, f"Erro ao exportar AST para DOT: {e}", tipo_erro="AVISO")


    def exportarAST_SVG(self, nome_arquivo_dot: str, nome_arquivo_svg: str):
        self.logger.info(f"Tentando exportar AST DOT para SVG: {nome_arquivo_svg}")
        if self.erro_handler.tem_erros_sintaticos: # Não tentar se houve erro sintático
            self.logger.warning("Não foi possível gerar SVG devido a erros sintáticos anteriores.")
            return
        try:
            subprocess.run(['dot', '-Tsvg', nome_arquivo_dot, '-o', nome_arquivo_svg], check=True, capture_output=True, text=True)
            self.logger.info(f"AST exportada com sucesso para {nome_arquivo_svg} usando Graphviz.")
        except FileNotFoundError:
            self.logger.warning("Comando 'dot' (Graphviz) não encontrado. Não foi possível gerar SVG.")
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, "Graphviz (dot) não está instalado ou no PATH. SVG não gerado.", tipo_erro="AVISO")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr or str(e)
            self.logger.error(f"Erro ao executar Graphviz para gerar SVG: {error_message}")
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, f"Erro do Graphviz ao gerar SVG: {error_message}", tipo_erro="AVISO")
        except Exception as e:
            self.erro_handler.registrar_erro("Analisador Sintático", 0, 0, f"Erro inesperado ao exportar AST para SVG: {e}", tipo_erro="AVISO")
