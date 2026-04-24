# Generated from miniportugol.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .miniportugolParser import miniportugolParser
else:
    from miniportugolParser import miniportugolParser

# This class defines a complete listener for a parse tree produced by miniportugolParser.
class miniportugolListener(ParseTreeListener):

    # Enter a parse tree produced by miniportugolParser#program.
    def enterProgram(self, ctx:miniportugolParser.ProgramContext):
        pass

    # Exit a parse tree produced by miniportugolParser#program.
    def exitProgram(self, ctx:miniportugolParser.ProgramContext):
        pass


    # Enter a parse tree produced by miniportugolParser#expr.
    def enterExpr(self, ctx:miniportugolParser.ExprContext):
        pass

    # Exit a parse tree produced by miniportugolParser#expr.
    def exitExpr(self, ctx:miniportugolParser.ExprContext):
        pass


    # Enter a parse tree produced by miniportugolParser#termo.
    def enterTermo(self, ctx:miniportugolParser.TermoContext):
        pass

    # Exit a parse tree produced by miniportugolParser#termo.
    def exitTermo(self, ctx:miniportugolParser.TermoContext):
        pass


    # Enter a parse tree produced by miniportugolParser#NUMERO.
    def enterNUMERO(self, ctx:miniportugolParser.NUMEROContext):
        pass

    # Exit a parse tree produced by miniportugolParser#NUMERO.
    def exitNUMERO(self, ctx:miniportugolParser.NUMEROContext):
        pass


    # Enter a parse tree produced by miniportugolParser#STRING.
    def enterSTRING(self, ctx:miniportugolParser.STRINGContext):
        pass

    # Exit a parse tree produced by miniportugolParser#STRING.
    def exitSTRING(self, ctx:miniportugolParser.STRINGContext):
        pass


    # Enter a parse tree produced by miniportugolParser#VARIAVEL.
    def enterVARIAVEL(self, ctx:miniportugolParser.VARIAVELContext):
        pass

    # Exit a parse tree produced by miniportugolParser#VARIAVEL.
    def exitVARIAVEL(self, ctx:miniportugolParser.VARIAVELContext):
        pass


    # Enter a parse tree produced by miniportugolParser#PARENTESES.
    def enterPARENTESES(self, ctx:miniportugolParser.PARENTESESContext):
        pass

    # Exit a parse tree produced by miniportugolParser#PARENTESES.
    def exitPARENTESES(self, ctx:miniportugolParser.PARENTESESContext):
        pass


    # Enter a parse tree produced by miniportugolParser#bloco.
    def enterBloco(self, ctx:miniportugolParser.BlocoContext):
        pass

    # Exit a parse tree produced by miniportugolParser#bloco.
    def exitBloco(self, ctx:miniportugolParser.BlocoContext):
        pass


    # Enter a parse tree produced by miniportugolParser#condicao.
    def enterCondicao(self, ctx:miniportugolParser.CondicaoContext):
        pass

    # Exit a parse tree produced by miniportugolParser#condicao.
    def exitCondicao(self, ctx:miniportugolParser.CondicaoContext):
        pass


    # Enter a parse tree produced by miniportugolParser#lista_comandos.
    def enterLista_comandos(self, ctx:miniportugolParser.Lista_comandosContext):
        pass

    # Exit a parse tree produced by miniportugolParser#lista_comandos.
    def exitLista_comandos(self, ctx:miniportugolParser.Lista_comandosContext):
        pass


    # Enter a parse tree produced by miniportugolParser#declaracao_variavel.
    def enterDeclaracao_variavel(self, ctx:miniportugolParser.Declaracao_variavelContext):
        pass

    # Exit a parse tree produced by miniportugolParser#declaracao_variavel.
    def exitDeclaracao_variavel(self, ctx:miniportugolParser.Declaracao_variavelContext):
        pass


    # Enter a parse tree produced by miniportugolParser#comando_escreva.
    def enterComando_escreva(self, ctx:miniportugolParser.Comando_escrevaContext):
        pass

    # Exit a parse tree produced by miniportugolParser#comando_escreva.
    def exitComando_escreva(self, ctx:miniportugolParser.Comando_escrevaContext):
        pass


    # Enter a parse tree produced by miniportugolParser#comando_ler.
    def enterComando_ler(self, ctx:miniportugolParser.Comando_lerContext):
        pass

    # Exit a parse tree produced by miniportugolParser#comando_ler.
    def exitComando_ler(self, ctx:miniportugolParser.Comando_lerContext):
        pass


    # Enter a parse tree produced by miniportugolParser#comando_se.
    def enterComando_se(self, ctx:miniportugolParser.Comando_seContext):
        pass

    # Exit a parse tree produced by miniportugolParser#comando_se.
    def exitComando_se(self, ctx:miniportugolParser.Comando_seContext):
        pass


    # Enter a parse tree produced by miniportugolParser#comando_enquanto.
    def enterComando_enquanto(self, ctx:miniportugolParser.Comando_enquantoContext):
        pass

    # Exit a parse tree produced by miniportugolParser#comando_enquanto.
    def exitComando_enquanto(self, ctx:miniportugolParser.Comando_enquantoContext):
        pass


    # Enter a parse tree produced by miniportugolParser#comando_definir.
    def enterComando_definir(self, ctx:miniportugolParser.Comando_definirContext):
        pass

    # Exit a parse tree produced by miniportugolParser#comando_definir.
    def exitComando_definir(self, ctx:miniportugolParser.Comando_definirContext):
        pass


    # Enter a parse tree produced by miniportugolParser#tipos_variaveis.
    def enterTipos_variaveis(self, ctx:miniportugolParser.Tipos_variaveisContext):
        pass

    # Exit a parse tree produced by miniportugolParser#tipos_variaveis.
    def exitTipos_variaveis(self, ctx:miniportugolParser.Tipos_variaveisContext):
        pass


    # Enter a parse tree produced by miniportugolParser#expr_condicionais.
    def enterExpr_condicionais(self, ctx:miniportugolParser.Expr_condicionaisContext):
        pass

    # Exit a parse tree produced by miniportugolParser#expr_condicionais.
    def exitExpr_condicionais(self, ctx:miniportugolParser.Expr_condicionaisContext):
        pass



del miniportugolParser