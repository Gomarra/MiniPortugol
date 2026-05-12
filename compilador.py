# compilador.py
import logging
from erro import Erro
from analise_lexica import AnaliseLexica
from analise_sintatica import AnaliseSintatica
# from analise_semantica import AnaliseSemantica
# from geracao_tac import GeracaoTAC
# from geracao_llvm import GeracaoLLVM

class Compilador:
    def __init__(self, nome_arquivo_fonte: str):
        self.nome_arquivo_fonte = nome_arquivo_fonte
        self.logger = logging.getLogger(self.__class__.__name__) # Logger para a classe Compilador
        self.erro_handler = Erro()

        # Instanciar as fases, passando o manipulador de erros
        self.analise_lexica_mod = AnaliseLexica(self.erro_handler)
        self.analise_sintatica_mod = AnaliseSintatica(self.erro_handler)
        # self.analise_semantica_mod = AnaliseSemantica(self.erro_handler)
        # self.geracao_tac_mod = GeracaoTAC(self.erro_handler)
        # self.geracao_llvm_mod = GeracaoLLVM(self.erro_handler)

        self.logger.info(f"Compilador Portugoool inicializado para o arquivo: {nome_arquivo_fonte}")

    def compilar(self):
        self.logger.info(f"--- Iniciando compilação de {self.nome_arquivo_fonte} ---")

        # Fase 1: Análise Léxica
        self.logger.info("--- FASE: Análise Léxica ---")
        tokens_log, token_stream = self.analise_lexica_mod.executarAnaliseLexica(self.nome_arquivo_fonte)
        if self.erro_handler.tem_erros_lexicos or not token_stream:
            self.logger.error("Compilação interrompida devido a erros léxicos.")
            return False

        # Fase 2: Análise Sintática
        self.logger.info("--- FASE: Análise Sintática ---")
        ast = self.analise_sintatica_mod.executarAnaliseSintatica(token_stream)
        if self.erro_handler.tem_erros_sintaticos or not ast:
            self.logger.error("Compilação interrompida devido a erros sintáticos.")
            return False
        # Exportar AST (opcional, mas útil para depuração)
        base_nome_arquivo = self.nome_arquivo_fonte.rsplit('.', 1)[0]
        self.analise_sintatica_mod.exportarAST_DOT(ast, base_nome_arquivo + ".dot")
        self.analise_sintatica_mod.exportarAST_SVG(base_nome_arquivo + ".dot", base_nome_arquivo + ".svg")

        # Fase 3: Análise Semântica
        # self.logger.info("--- FASE: Análise Semântica ---")
        # ast_anotada = self.analise_semantica_mod.executarAnaliseSemantica(ast)
        # if self.erro_handler.tem_erros_semanticos or not ast_anotada:
        #     self.logger.error("Compilação interrompida devido a erros semânticos.")
        #     return False

        # Fase 4: Geração de Código de Três Endereços (TAC)
        # self.logger.info("--- FASE: Geração de Código de Três Endereços (TAC) ---")
        # codigo_tac = self.geracao_tac_mod.gerarCodigoTAC(ast_anotada)
        # if self.erro_handler.tem_erros_tac or not codigo_tac:
        #     self.logger.error("Compilação interrompida devido a erros na geração do TAC.")
        #     return False

        # # Fase 5: Geração de Código LLVM
        # self.logger.info("--- FASE: Geração de Código LLVM IR ---")
        # codigo_llvm = self.geracao_llvm_mod.gerarCodigoLLVM(codigo_tac)
        # if self.erro_handler.tem_erros_llvm or not codigo_llvm:
        #     self.logger.error("Compilação interrompida devido a erros na geração do LLVM IR.")
        #     return False

        # self.logger.info("--- Compilação concluída com sucesso! ---")
        # try:
        #     with open(base_nome_arquivo + ".ll", "w", encoding='utf-8') as f:
        #         f.write(codigo_llvm)
        #     self.logger.info(f"Código LLVM IR salvo em: {base_nome_arquivo}.ll")
        # except IOError as e:
        #     self.erro_handler.registrar_erro("Compilador",0,0,f"Erro ao salvar arquivo LLVM: {e}", "GERAL")
        #     return False
        return True