grammar miniportugol;

program
    : declaracao_variavel* lista_comandos* EOF
    ;

/* Definição de expressões */
expr: termo ( (MAIS | MENOS) termo )*;
termo: fator ( (MULT | DIV) fator )*;
fator: INT          # NUMERO
     | STRING       # STRING
     | ID           # VARIAVEL
     | AP expr FP   # PARENTESES
     ; 

/* Blocos */
bloco: AC lista_comandos* FC;
condicao: expr expr_condicionais expr;

/* Comandos */
lista_comandos: comando_escreva
              | comando_ler
              | comando_se
              | comando_enquanto
              | comando_definir
              ;

declaracao_variavel: tipos_variaveis ID (VIRGULA ID)* PV;

comando_escreva: ESCREVA AP expr FP PV;
comando_ler: LEIA AP ID FP PV;

comando_se: SE AP condicao FP bloco (SENAO bloco)?;
comando_enquanto: ENQUANTO AP condicao FP bloco;

comando_definir: ID IGUAL expr (',' expr)* PV;

tipos_variaveis: VAR_INT
               | VAR_STRING
               ;

expr_condicionais:
                 |COND_IGUAL
                 |COND_DIF
                 |COND_E
                 |COND_OU
                 |COND_MAIOR
                 |COND_MENOR
                 ;

/* Tokens */
WS: [ \t\r\n]+ -> skip;

LEIA:'leia';
ESCREVA:'escreva';
SE:'se';
SENAO:'senao';
ENQUANTO:'enquanto';

VAR_INT: 'INT';
VAR_STRING: 'String';

MULT:'*';
DIV:'/';
MAIS:'+';
MENOS:'-';

COND_IGUAL:'==';
COND_DIF:'!=';
COND_E:'&&';
COND_OU:'||';
COND_MAIOR:'>';
COND_MENOR:'<';

IGUAL:'=';
AP:'(';
FP:')';
PV:';';
AC:'{';
FC:'}';
VIRGULA:',';

ID: [a-zA-Z_] [a-zA-Z0-9_]* ;
INT: [0-9]+;
STRING: '"' .*? '"' ;
