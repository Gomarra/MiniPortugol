# geracao_tac.py
import logging
from erro import Erro
from miniportugolParser import miniportugolParser

class GeracaoTAC:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.codigo_tac = []
        self.contador_temporarias = 0

    def _nova_temporaria(self) -> str:
        temp_nome = f"t{self.contador_temporarias}"
        self.contador_temporarias += 1
        return temp_nome

    def _gerar_tac_expr_recursivo(self, expr_node_ctx) -> str:
        node_text_for_log = expr_node_ctx.getText() if expr_node_ctx and hasattr(expr_node_ctx, 'getText') else 'CTX_EXPR_INVALIDO'
        # Removido o log INFO inicial daqui para reduzir verbosidade, logs de casos específicos são mais úteis.
        # self.logger.info(f"GER_TAC_EXPR: Entrando para '{node_text_for_log}', tipo de nó: {type(expr_node_ctx)}")

        if isinstance(expr_node_ctx, miniportugolParser.NumberContext):
            val = expr_node_ctx.NUMBER().getText()
            self.logger.info(f"GER_TAC_EXPR: Number literal: {val}")
            return val
        
        if isinstance(expr_node_ctx, miniportugolParser.StringContext):
            val = expr_node_ctx.STRING().getText()
            self.logger.info(f"GER_TAC_EXPR: String literal: {val}")
            return val
            
        if isinstance(expr_node_ctx, miniportugolParser.VariableContext):
            val = expr_node_ctx.ID().getText()
            self.logger.info(f"GER_TAC_EXPR: Variable: {val}")
            return val
            
        if isinstance(expr_node_ctx, miniportugolParser.ParenthesesContext):
            self.logger.info(f"GER_TAC_EXPR: Parentheses, processando expr interna '{expr_node_ctx.expr().getText()}'...")
            return self._gerar_tac_expr_recursivo(expr_node_ctx.expr())

        if isinstance(expr_node_ctx, miniportugolParser.TermContext) or isinstance(expr_node_ctx, miniportugolParser.ExprContext):
            children = expr_node_ctx.children
            operando_esq_ctx = children[0]
            operando_esq_nome = self._gerar_tac_expr_recursivo(operando_esq_ctx)

            num_operacoes = (len(children) - 1) // 2
            for i in range(num_operacoes):
                operador_node = children[i * 2 + 1]
                operando_dir_ctx = children[i * 2 + 2]
                operador = operador_node.getText()
                operando_dir_nome = self._gerar_tac_expr_recursivo(operando_dir_ctx)
                
                if operando_esq_nome.startswith("ERRO_") or operando_dir_nome.startswith("ERRO_"):
                    self.logger.error(f"GER_TAC_EXPR (op): Erro em um dos operandos para '{operador_node.getText()}' - Esq: {operando_esq_nome}, Dir: {operando_dir_nome}")
                    # Se um operando já é um erro, o resultado da expressão inteira é um erro.
                    # Retornar um erro específico ajuda a não gerar mais TAC para esta subárvore.
                    return "ERRO_TAC_OPERAND" 
                
                temp_dest = self._nova_temporaria()
                self.codigo_tac.append(f"{temp_dest} := {operando_esq_nome} {operador} {operando_dir_nome}")
                self.logger.info(f"GER_TAC_EXPR (op): {temp_dest} := {operando_esq_nome} {operador} {operando_dir_nome}")
                operando_esq_nome = temp_dest
            return operando_esq_nome

        if isinstance(expr_node_ctx, miniportugolParser.FactorContext):
             if expr_node_ctx.getChildCount() == 1:
                 return self._gerar_tac_expr_recursivo(expr_node_ctx.getChild(0))

        self.logger.error(f"GER_TAC_EXPR: Tipo de nó de expressão não suportado para TAC: {type(expr_node_ctx)} com texto '{node_text_for_log}'")
        self.erro_handler.registrar_erro("Gerador TAC", 
                                         expr_node_ctx.start.line if expr_node_ctx else 0, 
                                         expr_node_ctx.start.column + 1 if expr_node_ctx else 0,
                                         f"Tipo de expressão não suportado para TAC: {type(expr_node_ctx)}.", "TAC")
        return "ERRO_TAC_EXPR_TYPE"

    def gerarCodigoTAC(self, ast_validada):
        self.logger.info("Iniciando geração de Código de Três Endereços (TAC)...")
        if not ast_validada or self.erro_handler.houve_erro_fatal():
            self.logger.error("AST validada não fornecida ou erros anteriores impedem geração de TAC.")
            return None
        self.codigo_tac = []
        self.contador_temporarias = 0

        try:
            for stmt_geral_ctx in ast_validada.stmt(): 
                ctx_da_label = stmt_geral_ctx.getChild(0) # Este é o contexto da Label (ex: PrintStmtContext)
                
                self.logger.info(f"GER_TAC_STMT_DEBUG: Processando statement. Tipo do ctx_da_label: {type(ctx_da_label)}")

                if isinstance(ctx_da_label, miniportugolParser.InputStmtContext):
                    # ctx_da_label JÁ É o InputStmtContext (contexto da regra inputStmt)
                    var_nome = ctx_da_label.ID().getText() # Acesso direto
                    self.codigo_tac.append(f"INPUT {var_nome}")
                    self.logger.info(f"TAC: INPUT {var_nome}")

                elif isinstance(ctx_da_label, miniportugolParser.PrintStmtContext):
                    # ctx_da_label JÁ É o PrintStmtContext (contexto da regra printStmt)
                    # Acessamos exprList diretamente dele
                    if hasattr(ctx_da_label, 'exprList') and ctx_da_label.exprList() and hasattr(ctx_da_label.exprList(), 'expr'):
                        for expr_item_ctx in ctx_da_label.exprList().expr():
                            val_expr_tac = self._gerar_tac_expr_recursivo(expr_item_ctx)
                            if val_expr_tac.startswith("ERRO_"):
                                 self.logger.error(f"TAC: Erro ao gerar TAC para expressão em PRINT: {expr_item_ctx.getText()}")
                            else:
                                self.codigo_tac.append(f"PRINT {val_expr_tac}")
                                self.logger.info(f"TAC: PRINT {val_expr_tac}")
                    else:
                        self.logger.error(f"TAC: Estrutura inesperada para PrintStmtContext, exprList não encontrada: {ctx_da_label.getText()}")
                        self.erro_handler.registrar_erro("Gerador TAC", ctx_da_label.start.line, ctx_da_label.start.column + 1, "Estrutura interna do PRINT inválida para TAC.", "TAC")

                
                elif isinstance(ctx_da_label, miniportugolParser.LetStmtContext):
                    # ctx_da_label JÁ É o LetStmtContext (contexto da regra letStmt)
                    var_nome = ctx_da_label.ID().getText() # Acesso direto
                    expr_node_atribuicao = ctx_da_label.expr() # Acesso direto
                    
                    val_expr_tac = self._gerar_tac_expr_recursivo(expr_node_atribuicao)
                    if val_expr_tac.startswith("ERRO_"):
                        self.logger.error(f"TAC: Erro ao gerar TAC para expressão em LET {var_nome}: {expr_node_atribuicao.getText()}")
                    else:
                        self.codigo_tac.append(f"{var_nome} := {val_expr_tac}")
                        self.logger.info(f"TAC: {var_nome} := {val_expr_tac}")
                else:
                    self.logger.warning(f"Geração TAC não implementada para o tipo de statement (label context): {type(ctx_da_label)} com texto '{ctx_da_label.getText() if hasattr(ctx_da_label, 'getText') else 'N/A'}'")
        
        except Exception as e:
            self.erro_handler.registrar_erro("Gerador TAC", 0, 0, f"Erro inesperado na geração TAC: {e}", "TAC")
            self.logger.exception("Detalhes da exceção na geração TAC:")
            return None

        if not self.erro_handler.tem_erros_tac:
            self.logger.info("Geração de TAC concluída.")
        else:
            self.logger.error("Geração de TAC encontrou erros.")
        
        self.logger.info("--- Código TAC Gerado ---")
        if not self.codigo_tac:
            self.logger.info("  (Nenhum código TAC gerado)")
        else:
            for instrucao_idx, instrucao in enumerate(self.codigo_tac):
                self.logger.info(f"  {instrucao_idx}: {instrucao}")
        self.logger.info("-------------------------")
        
        return self.codigo_tac