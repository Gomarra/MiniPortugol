# analise_semantica.py
import logging
import sys # Importar sys para print de depuração
from antlr4 import ParseTreeWalker
from miniportugolParser import miniportugolParser
from miniportugolListener import miniportugolListener
from erro import Erro

class miniportugolSemanticoListenerImpl(miniportugolListener):
    # ... (init, _registrar_variavel_declarada, _verificar_uso_variavel como antes) ...
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.escopo_atual = {} 
        self.variaveis_declaradas_globalmente = set()
        self.ast_anotada = None

    def _registrar_variavel_declarada(self, nome_var: str, tipo_var: str, rule_node_ctx):
        id_node_symbol = None
        if hasattr(rule_node_ctx, 'ID') and callable(rule_node_ctx.ID) and rule_node_ctx.ID():
            id_node_symbol = rule_node_ctx.ID().getSymbol()
        
        line = id_node_symbol.line if id_node_symbol else rule_node_ctx.start.line
        column = (id_node_symbol.column + 1) if id_node_symbol else (rule_node_ctx.start.column + 1)

        self.logger.info(f"Variável '{nome_var}' (tipo: {tipo_var}) definida/declarada na linha {line}, coluna {column}.")
        self.variaveis_declaradas_globalmente.add(nome_var)
        self.escopo_atual[nome_var] = {
            "linha": line,
            "coluna": column,
            "usada": False,
            "type_name": tipo_var
        }
        if id_node_symbol:
             id_node_symbol.type_name = tipo_var


    def _verificar_uso_variavel(self, nome_var: str, id_symbol):
        line = id_symbol.line
        column = id_symbol.column + 1
        if nome_var not in self.escopo_atual:
            msg = f"Variável '{nome_var}' usada antes de ser definida/declarada."
            self.erro_handler.registrar_erro("Analisador Semântico", line, column, msg, tipo_erro="SEMANTICO")
            return None 
        
        var_info = self.escopo_atual[nome_var]
        var_info["usada"] = True 
        self.logger.info(f"Variável '{nome_var}' (tipo: {var_info['type_name']}) usada na linha {line}, coluna {column}.")
        return var_info["type_name"]

    def exitNumero(self, ctx: miniportugolParser.NumeroContext):
        print(f"DEBUG_PRINT_CALL: Entrando em exitNumero para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        ctx.type_name = "NUMERO"
        self.logger.info(f"EXIT_NUMERO: ctx ID: {id(ctx)}, Texto: '{ctx.getText()}', Tipo definido: {ctx.type_name}")

    def exitString(self, ctx: miniportugolParser.StringContext):
        print(f"DEBUG_PRINT_CALL: Entrando em exitString para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        ctx.type_name = "STRING"
        self.logger.info(f"EXIT_STRING: ctx ID: {id(ctx)}, Texto: '{ctx.getText()}', Tipo definido: {ctx.type_name}")

    def exitVariavel(self, ctx: miniportugolParser.VariavelContext):
        print(f"DEBUG_PRINT_CALL: Entrando em exitVariavel para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        nome_var = ctx.ID().getText()
        id_symbol = ctx.ID().getSymbol()
        tipo_var = self._verificar_uso_variavel(nome_var, id_symbol) 
        ctx.type_name = tipo_var if tipo_var else "ERRO_TIPO"
        if id_symbol and tipo_var : 
            id_symbol.type_name = ctx.type_name 
        self.logger.info(f"EXIT_VARIAVEL: ctx ID: {id(ctx)}, Texto: '{nome_var}', Tipo obtido: {ctx.type_name}")

    def exitParenteses(self, ctx: miniportugolParser.ParentesesContext):
        print(f"DEBUG_PRINT_CALL: Entrando em exitParenteses para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        # Restante da lógica como antes...
        self.logger.info(f"EXIT_PARENTESES: Entrando para '{ctx.getText()}'. ctx ID: {id(ctx)}.")
        inner_expr_ctx = ctx.expr()
        if hasattr(inner_expr_ctx, 'type_name'):
            ctx.type_name = inner_expr_ctx.type_name
            self.logger.info(f"EXIT_PARENTESES: Tipo propagado de expr interna: {ctx.type_name}")
        else:
            self.logger.error(f"EXIT_PARENTESES: Expressão interna de '{ctx.getText()}' não tem 'type_name'.")
            ctx.type_name = "ERRO_TIPO"
        self.logger.info(f"EXIT_PARENTESES: Texto: '{ctx.getText()}', Tipo final: {ctx.type_name}")


    def exitFactor(self, ctx: miniportugolParser.FactorContext):
        # Adiciona o print de depuração como a PRIMEIRA linha
        print(f"DEBUG_PRINT_CALL: Entrando em exitFactor para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        # Restante da lógica como antes...
        self.logger.info(f"EXIT_FACTOR: Entrando para Factor '{ctx.getText()}'. ctx ID: {id(ctx)}. Tipo do ctx: {type(ctx)}")
        if hasattr(ctx, 'type_name'):
            self.logger.info(f"EXIT_FACTOR: 'type_name' já existe e é '{ctx.type_name}'. (Definido por listener específico como exitString).")
        else:
            self.logger.error(f"EXIT_FACTOR: ERRO DE LÓGICA DO LISTENER! Nó Factor '{ctx.getText()}' (tipo {type(ctx)}) não teve 'type_name' definido. Verifique os listeners das alternativas de 'factor' (exitString, exitNumero, etc.).")
            ctx.type_name = "ERRO_FACTOR_INESPERADO"

    def exitTerm(self, ctx: miniportugolParser.TermContext):
        # Adiciona o print de depuração como a PRIMEIRA linha
        print(f"DEBUG_PRINT_CALL: Entrando em exitTerm para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        # Restante da lógica como antes...
        self.logger.info(f"EXIT_TERM: Entrando para Term '{ctx.getText()}'. ctx ID: {id(ctx)}.")
        current_type = "ERRO_TIPO" 
        primeiro_fator = ctx.factor(0)
        if primeiro_fator:
            self.logger.info(f"EXIT_TERM: Acessando primeiro_fator '{primeiro_fator.getText()}' com ID: {id(primeiro_fator)}")
            if hasattr(primeiro_fator, 'type_name'):
                current_type = primeiro_fator.type_name
                self.logger.info(f"EXIT_TERM: primeiro_fator tinha 'type_name': {current_type}")
            else:
                self.logger.error(f"EXIT_TERM: ERRO DE PROPAGAÇÃO! Primeiro fator de Term '{ctx.getText()}' (texto: '{primeiro_fator.getText()}') NÃO tem 'type_name'.")
        else:
            self.logger.error(f"EXIT_TERM: ERRO ESTRUTURAL! Term '{ctx.getText()}' não tem primeiro fator ctx.factor(0).")

        num_factors = len(ctx.factor())
        if num_factors > 1 and current_type != "ERRO_TIPO" and not current_type.startswith("ERRO_"):
            for i in range(num_factors - 1):
                op_node = ctx.getChild(i * 2 + 1); op_text = op_node.getText()
                right_operand_ctx = ctx.factor(i + 1)
                right_operand_type = "ERRO_TIPO"
                if hasattr(right_operand_ctx, 'type_name'): right_operand_type = right_operand_ctx.type_name
                else: self.logger.error(f"EXIT_TERM: ERRO DE PROPAGAÇÃO! Fator direito (índice {i+1}, texto: '{right_operand_ctx.getText()}') de Term '{ctx.getText()}' não tem 'type_name'.")
                if right_operand_type == "ERRO_TIPO" or right_operand_type.startswith("ERRO_"): current_type = "ERRO_TIPO"; break 
                if op_text in ['*', '/']:
                    if current_type == "NUMERO" and right_operand_type == "NUMERO": current_type = "NUMERO"
                    else: msg = f"Operador '{op_text}' requer operandos numéricos. Obtidos: {current_type} e {right_operand_type}."; self.erro_handler.registrar_erro("Analisador Semântico", op_node.symbol.line, op_node.symbol.column + 1, msg, "SEMANTICO"); current_type = "ERRO_TIPO"; break
        ctx.type_name = current_type
        self.logger.info(f"EXIT_TERM: Tipo final inferido para Term '{ctx.getText()}': {ctx.type_name}")


    def exitExpr(self, ctx: miniportugolParser.ExprContext):
        # Adiciona o print de depuração como a PRIMEIRA linha
        print(f"DEBUG_PRINT_CALL: Entrando em exitExpr para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        # Restante da lógica como antes...
        self.logger.info(f"EXIT_EXPR: Entrando para Expr '{ctx.getText()}'. ctx ID: {id(ctx)}.")
        current_type = "ERRO_TIPO"
        primeiro_termo = ctx.termo(0)
        if primeiro_termo:
            self.logger.info(f"EXIT_EXPR: Acessando primeiro_termo '{primeiro_termo.getText()}' com ID: {id(primeiro_termo)}")
            if hasattr(primeiro_termo, 'type_name'): current_type = primeiro_termo.type_name; self.logger.info(f"EXIT_EXPR: primeiro_termo tinha 'type_name': {current_type}")
            else: self.logger.error(f"EXIT_EXPR: ERRO DE PROPAGAÇÃO! Primeiro termo de Expr '{ctx.getText()}' (texto: '{primeiro_termo.getText()}') NÃO tem 'type_name'.")
        else: self.logger.error(f"EXIT_EXPR: ERRO ESTRUTURAL! Expr '{ctx.getText()}' não tem primeiro termo ctx.termo(0).")

        num_terms = len(ctx.termo())
        if num_terms > 1 and current_type != "ERRO_TIPO" and not current_type.startswith("ERRO_"): 
            for i in range(num_terms - 1):
                op_node = ctx.getChild(i * 2 + 1); op_text = op_node.getText()
                right_operand_ctx = ctx.termo(i + 1)
                right_operand_type = "ERRO_TIPO" 
                if hasattr(right_operand_ctx, 'type_name'): right_operand_type = right_operand_ctx.type_name
                else: self.logger.error(f"EXIT_EXPR: ERRO DE PROPAGAÇÃO! Termo direito (índice {i+1}, texto: '{right_operand_ctx.getText()}') de Expr '{ctx.getText()}' não tem 'type_name'.")
                if right_operand_type == "ERRO_TIPO" or right_operand_type.startswith("ERRO_"): current_type = "ERRO_TIPO"; break
                if op_text in ['+', '-']:
                    if current_type == "NUMERO" and right_operand_type == "NUMERO": current_type = "NUMERO"
                    else: msg = (f"Operador '{op_text}' requer operandos numéricos. Obtidos: {current_type} e {right_operand_type}."); self.erro_handler.registrar_erro("Analisador Semântico", op_node.symbol.line, op_node.symbol.column + 1, msg, "SEMANTICO"); current_type = "ERRO_TIPO"; break
        ctx.type_name = current_type
        self.logger.info(f"EXIT_EXPR: Tipo final inferido para Expr '{ctx.getText()}': {ctx.type_name}")

    # --- Métodos de Statement ---
    def exitLetStatement(self, ctx:miniportugolParser.LetStatementContext): 
        print(f"DEBUG_PRINT_CALL: Entrando em exitLetStatement para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        actual_let_stmt_ctx = ctx.letStmt() 
        nome_var = actual_let_stmt_ctx.ID().getText()
        expr_node = actual_let_stmt_ctx.expr()
        tipo_expr = expr_node.type_name if hasattr(expr_node, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"Analisando semanticamente: LET {nome_var} = [expr tipo: {tipo_expr}]")
        if tipo_expr.startswith("ERRO_"):
            self.erro_handler.registrar_erro("Analisador Semântico", expr_node.start.line, expr_node.start.column + 1, f"Expressão no lado direito de LET para '{nome_var}' contém erro de tipo ou tipo não pôde ser determinado.", "SEMANTICO")
            self._registrar_variavel_declarada(nome_var, "ERRO_TIPO", actual_let_stmt_ctx) 
            return
        if nome_var in self.escopo_atual:
            self.logger.info(f"Variável '{nome_var}' está sendo reatribuída. Tipo anterior: {self.escopo_atual[nome_var]['type_name']}, Novo tipo da expressão: {tipo_expr}.")
            self.escopo_atual[nome_var]['type_name'] = tipo_expr
        else:
            self._registrar_variavel_declarada(nome_var, tipo_expr, actual_let_stmt_ctx)
        if nome_var in self.escopo_atual: self.escopo_atual[nome_var]["usada_como_alvo"] = True

    def exitInputStatement(self, ctx:miniportugolParser.InputStatementContext): 
        print(f"DEBUG_PRINT_CALL: Entrando em exitInputStatement para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        actual_input_stmt_ctx = ctx.inputStmt() 
        nome_var = actual_input_stmt_ctx.ID().getText()
        tipo_input = "NUMERO" 
        self.logger.info(f"Analisando semanticamente: INPUT {nome_var} (será tipo: {tipo_input})")
        if nome_var in self.escopo_atual:
            self.logger.info(f"Variável '{nome_var}' (para INPUT) está sendo reusada/reatribuída.")
            self.escopo_atual[nome_var]['type_name'] = tipo_input
        else:
            self._registrar_variavel_declarada(nome_var, tipo_input, actual_input_stmt_ctx)
        if nome_var in self.escopo_atual: self.escopo_atual[nome_var]["usada_como_alvo"] = True

    def exitPrintStatement(self, ctx:miniportugolParser.PrintStatementContext): 
        print(f"DEBUG_PRINT_CALL: Entrando em exitPrintStatement para '{ctx.getText() if ctx and hasattr(ctx, 'getText') else 'CTX_INVALIDO'}'", file=sys.stderr)
        self.logger.info(f"DEBUG_PRINT: Entrando em exitPrintStatement. Tipo do ctx: {type(ctx)}, ID do ctx: {id(ctx)}")
        actual_print_stmt_ctx = None
        if hasattr(ctx, 'printStmt') and callable(ctx.printStmt): actual_print_stmt_ctx = ctx.printStmt()
        if not actual_print_stmt_ctx:
            self.logger.error(f"DEBUG_PRINT CRITICAL: Não foi possível acessar 'printStmt()' a partir do contexto ({type(ctx)}) do statement PRINT.")
            self.erro_handler.registrar_erro("Analisador Semântico", ctx.start.line, ctx.start.column + 1, "Falha interna: Estrutura do comando PRINT (acesso ao ctx da regra printStmt).", "SEMANTICO")
            return
        if not hasattr(actual_print_stmt_ctx, 'exprList') or not actual_print_stmt_ctx.exprList():
            self.logger.error(f"DEBUG_PRINT CRITICAL: 'actual_print_stmt_ctx' ({type(actual_print_stmt_ctx)}) NÃO TEM o atributo 'exprList' ou ele é None.")
            self.erro_handler.registrar_erro("Analisador Semântico", actual_print_stmt_ctx.start.line, actual_print_stmt_ctx.start.column + 1, "Falha interna: Estrutura do comando PRINT (ausência de exprList).", "SEMANTICO")
            return 
        self.logger.info(f"Analisando semanticamente: PRINT (processando lista de expressões)")
        expr_list_node = actual_print_stmt_ctx.exprList()
        for expr_item_ctx in expr_list_node.expr(): 
            tipo_expr_item = "ERRO_TIPO_DEFAULT_PRINT"
            if hasattr(expr_item_ctx, 'type_name'):
                tipo_expr_item = expr_item_ctx.type_name
                self.logger.info(f"DEBUG_PRINT: Expressão '{expr_item_ctx.getText()}' (ID: {id(expr_item_ctx)}) tem 'type_name': {tipo_expr_item}")
            else:
                self.logger.error(f"DEBUG_PRINT: Expressão '{expr_item_ctx.getText()}' (ID: {id(expr_item_ctx)}) NÃO tem 'type_name' ao ser lida no PRINT.")
            self.logger.info(f"  Item para PRINT: '{expr_item_ctx.getText()}', Tipo inferido FINAL: {tipo_expr_item}")
            if tipo_expr_item.startswith("ERRO_"):
                self.erro_handler.registrar_erro("Analisador Semântico", expr_item_ctx.start.line, expr_item_ctx.start.column + 1, f"Expressão '{expr_item_ctx.getText()}' no comando PRINT contém erro de tipo ou tipo não pôde ser determinado ({tipo_expr_item}).", "SEMANTICO")

    def exitProg(self, ctx:miniportugolParser.ProgContext):
        print(f"DEBUG_PRINT_CALL: Entrando em exitProg", file=sys.stderr) # Adicionado para consistência
        self.logger.info("--- Verificação Final Semântica ---")
        for nome_var, info_var in self.escopo_atual.items():
            if not info_var["usada"] and not info_var.get("usada_como_alvo", False): msg = f"Variável '{nome_var}' declarada na linha {info_var['linha']} mas seu valor nunca é lido/utilizado."; self.erro_handler.registrar_erro("Analisador Semântico", info_var['linha'], info_var['coluna'], msg, tipo_erro="AVISO_SEMANTICO")
            elif not info_var["usada"] and info_var.get("usada_como_alvo", False): msg = f"Valor da variável '{nome_var}' (definida na linha {info_var['linha']}) nunca é lido/utilizado."; self.erro_handler.registrar_erro("Analisador Semântico", info_var['linha'], info_var['coluna'], msg, tipo_erro="AVISO_SEMANTICO")
        self.logger.info("Análise semântica concluída (com possíveis avisos/erros).")
        self.ast_anotada = ctx

# --- Classe AnaliseSemantica (Wrapper) ---
class AnaliseSemantica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ast_anotada = None
    def executarAnaliseSemantica(self, ast_parser):
        self.logger.info("Iniciando análise semântica...")
        if not ast_parser: self.logger.error("AST não fornecida pelo parser. Análise semântica não pode prosseguir."); return None
        if self.erro_handler.houve_erro_fatal(): self.logger.warning("Erros fatais detectados em fases anteriores. Análise semântica pulada."); return ast_parser 
        try:
            listener_semantico = miniportugolSemanticoListenerImpl(self.erro_handler)
            walker = ParseTreeWalker()
            walker.walk(listener_semantico, ast_parser) 
            self.ast_anotada = listener_semantico.ast_anotada 
            if not self.erro_handler.tem_erros_semanticos: self.logger.info("Análise semântica concluída com sucesso (sem erros fatais semânticos).")
            else: self.logger.error("Análise semântica encontrou ERROS.")
            return self.ast_anotada 
        except Exception as e:
            self.erro_handler.registrar_erro("Analisador Semântico", 0, 0, f"Erro inesperado e crítico na análise semântica: {e}", tipo_erro="SEMANTICO")
            self.logger.exception("Detalhes da exceção crítica na análise semântica:")
            return ast_parser