# analise_lexica.py
import logging
from antlr4 import FileStream, CommonTokenStream, Token
from miniportugolLexer import miniportugolLexer # Arquivo gerado pelo ANTLR
from erro import Erro, CustomErrorListener # Do nosso arquivo erro.py

class AnaliseLexica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.lista_tokens = []

    def _log_tokens(self, lexer: miniportugolLexer):
        temp_lexer = miniportugolLexer(lexer.inputStream)
        temp_lexer.removeErrorListeners()
        
        token = temp_lexer.nextToken()
        self.lista_tokens = []
        while token.type != Token.EOF:
            token_name = ""
            try:
                # Tenta obter o nome simbólico. Mais robusto.
                token_name = temp_lexer.vocabulary.getSymbolicName(token.type)
                if token_name is None: # Se for None, pode ser um literal sem nome simbólico explícito
                    token_name = temp_lexer.vocabulary.getLiteralName(token.type)
                    if token_name is None: # Fallback
                        token_name = f"TYPE_{token.type}"
                    else: # Remove aspas de literais, ex: "'PRINT'" -> "PRINT"
                        if token_name.startswith("'") and token_name.endswith("'"):
                            token_name = token_name[1:-1]
            except Exception: # Fallback genérico
                 token_name = f"TYPE_{token.type}"

            self.logger.info(f"Token: {token_name}, Texto: '{token.text}', Linha: {token.line}, Coluna: {token.column+1}")
            self.lista_tokens.append(token) # Movido para dentro do loop para incluir todos os tokens antes do EOF
            token = temp_lexer.nextToken()
        
        self.lista_tokens.append(token) # Adiciona o token EOF
        eof_symbol_name = "EOF"
        try:
            eof_symbol_name = temp_lexer.vocabulary.getSymbolicName(token.type) or "EOF"
        except Exception:
            pass # Mantém "EOF" como fallback
        self.logger.info(f"Token: {eof_symbol_name}, Texto: '{token.text}', Linha: {token.line}, Coluna: {token.column+1}")


    def executarAnaliseLexica(self, nome_arquivo_fonte: str):
        self.logger.info(f"Iniciando análise léxica do arquivo: {nome_arquivo_fonte}")
        try:
            # LINHA CORRIGIDA ABAIXO (era 'utf-')
            input_stream = FileStream(nome_arquivo_fonte, encoding='utf-8')
            lexer = miniportugolLexer(input_stream)
            lexer.removeErrorListeners()
            lexer.addErrorListener(CustomErrorListener(self.erro_handler, "Analisador Léxico"))

            # Para logar os tokens, criamos um novo FileStream e um novo Lexer
            # para não consumir o 'lexer' principal que será usado pelo CommonTokenStream.
            log_input_stream = FileStream(nome_arquivo_fonte, encoding='utf-8') # Também verificar esta linha
            log_lexer = miniportugolLexer(log_input_stream)
            self._log_tokens(log_lexer)

            # O 'lexer' original ainda não foi consumido e seu input_stream está no início.
            token_stream = CommonTokenStream(lexer)
            self.logger.info("Análise léxica concluída (stream de tokens pronto para o parser).")
            # Retorna a lista de tokens (para possível uso futuro ou verificação) e o stream para o parser.
            return self.lista_tokens, token_stream

        except FileNotFoundError:
            self.erro_handler.registrar_erro("Analisador Léxico", 0, 0, f"Arquivo fonte '{nome_arquivo_fonte}' não encontrado.", tipo_erro="LEXICO")
            return None, None
        except AttributeError as e:
            self.erro_handler.registrar_erro("Analisador Léxico", 0, 0, f"Erro de atributo na análise léxica: {e}", tipo_erro="LEXICO")
            self.logger.exception("Detalhes do AttributeError:")
            return None, None
        except Exception as e: # Captura outras exceções, incluindo SyntaxError se houver problema no arquivo ANTLR gerado.
            self.erro_handler.registrar_erro("Analisador Léxico", 0, 0, f"Erro inesperado na análise léxica: {e}", tipo_erro="LEXICO")
            self.logger.exception("Detalhes do erro inesperado:")
            return None, None