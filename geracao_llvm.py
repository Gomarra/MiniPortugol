# geracao_llvm.py
import logging
from erro import Erro
import re
import datetime

class GeracaoLLVM:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.codigo_llvm_linhas = []
        self.main_body_instructions = []
        self.global_definitions = []
        self.reg_count = 0
        self.var_map = {}  # Mapeia nome_miniportugol -> {"ptr_llvm": %ptr.nome, "type_llvm": "i32*" ou "ptr*"}
        self.global_str_count = 0

    def _nova_reg(self) -> str:
        reg = f"%r{self.reg_count}"
        self.reg_count += 1
        return reg

    def _sanitize_llvm_name(self, name: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9$._]', '_', name)
        if not sanitized or not (sanitized[0].isalpha() or sanitized[0] in ['$', '.', '_']):
            sanitized = "v_" + sanitized
        return sanitized

    def _get_var_alloc_instruction(self, var_name_miniportugol: str, llvm_type: str = "i32") -> str:
        """Prepara a instrução alloca para uma variável, mas não a adiciona ainda."""
        if var_name_miniportugol not in self.var_map:
            llvm_var_name_clean = self._sanitize_llvm_name(var_name_miniportugol)
            ptr_reg = f"%ptr.{llvm_var_name_clean}"
            # Guarda o tipo LLVM do ponteiro (ex: i32*, ou i8** se for ponteiro para string)
            self.var_map[var_name_miniportugol] = {"ptr_llvm": ptr_reg, "llvm_type_pointed_to": llvm_type}
            
            type_to_alloca = llvm_type
            align = 4
            if llvm_type == "i8*": # Se a variável vai guardar um ponteiro (para string)
                type_to_alloca = "i8*" # aloca um ponteiro para char (i8*)
                align = 8 # Ponteiros são geralmente alinhados a 8 em 64-bit
            
            return f"  {ptr_reg} = alloca {type_to_alloca}, align {align} ; Var {var_name_miniportugol} (tipo {type_to_alloca})"
        # Se já existe, apenas retorna o ponteiro já conhecido
        return self.var_map[var_name_miniportugol]["ptr_llvm"]


    def _nova_global_string_const(self, text_content: str) -> str:
        str_label = f"@.str.const.{self.global_str_count}"
        self.global_str_count += 1
        
        llvm_escaped_content = ""
        # Simples escape para LLVM IR string literal c"..."
        # LLVM lida com UTF-8 internamente se o source_filename for UTF-8
        # Apenas \ e " precisam de escape dentro de c"..."
        for char_val in text_content:
            if char_val == '"':
                llvm_escaped_content += '\\22'
            elif char_val == '\\':
                llvm_escaped_content += '\\5C'
            elif ord(char_val) < 32 or ord(char_val) > 126: # Não-ASCII imprimível simples
                # Para bytes UTF-8, convertemos cada byte.
                # Isso é mais complexo se quisermos \XX para cada byte de uma sequência UTF-8.
                # Por simplicidade, vamos deixar o LLVM interpretar o UTF-8 direto da string se possível.
                # A constante LLVM c"..." aceita UTF-8. O \00 é crucial.
                # Se o `clang` vai ler o .ll como UTF-8, então caracteres acentuados podem ir direto.
                # A forma com `\\{char_code:02X}` era para bytes individuais.
                llvm_escaped_content += char_val # Deixa o LLVM/Clang lidar com UTF-8 na string
            else:
                llvm_escaped_content += char_val
        llvm_escaped_content += "\\00" # Null terminator

        num_bytes = len(text_content.encode('utf-8')) + 1

        llvm_str_decl = f'{str_label} = private unnamed_addr constant [{num_bytes} x i8] c"{llvm_escaped_content}"'
        
        # Adiciona à lista de definições globais se ainda não existir (improvável com contador, mas seguro)
        if llvm_str_decl not in self.global_definitions:
            self.global_definitions.append(llvm_str_decl)
        return str_label

    def _load_operand(self, operand_tac: str) -> tuple[str, str]:
        self.logger.debug(f"LLVM_LOAD_OP: Processando operando TAC: '{operand_tac}'")
        if operand_tac.isdigit() or (operand_tac.startswith('-') and operand_tac[1:].isdigit()):
            self.logger.debug(f"LLVM_LOAD_OP: É i32 literal: {operand_tac}")
            return "i32", operand_tac
        
        elif operand_tac.startswith('"') and operand_tac.endswith('"'): 
            str_content = operand_tac[1:-1]
            global_str_label = self._nova_global_string_const(str_content)
            gep_reg = self._nova_reg()
            num_bytes = len(str_content.encode('utf-8')) + 1
            # GEP é uma instrução, vai para o corpo da main
            self.main_body_instructions.append(f"  {gep_reg} = getelementptr inbounds [{num_bytes} x i8], [{num_bytes} x i8]* {global_str_label}, i64 0, i64 0")
            self.logger.debug(f"LLVM_LOAD_OP: É string literal, GEP reg: {gep_reg} para {global_str_label}")
            return "i8*", gep_reg

        elif operand_tac.startswith("t"): 
            # Assume que temporárias tX já são resultados de i32 (ou ponteiros se de GEP)
            # Para simplificar, vamos assumir que se uma temp tX aparece como operando, ela já tem
            # o valor i32 em um registrador LLVM %tX.
            # Se a temp tX guardasse um ponteiro, precisaríamos de um tipo diferente.
            # Por agora, todas as temps de operações aritméticas são i32.
            self.logger.debug(f"LLVM_LOAD_OP: É temporária i32: %{operand_tac}")
            return "i32", f"%{operand_tac}" 
        
        else: # Variável de usuário
            # Precisa determinar o tipo da variável (i32 ou ptr para string)
            # Por enquanto, _get_var_ptr só aloca i32. Isso precisa ser melhorado.
            # Vamos assumir que se uma variável está sendo lida, é para um contexto i32.
            if operand_tac not in self.var_map:
                # Variável usada antes de ser definida/alocada (erro semântico já deveria ter pego)
                # Ou é uma variável que só aparecerá como destino (ex: INPUT)
                self.logger.warning(f"LLVM_LOAD_OP: Variável '{operand_tac}' não encontrada no var_map ao tentar carregar. Assumindo i32 e alocando agora.")
                # Isso pode ser problemático se ela deveria ser de outro tipo.
                # A análise semântica deveria anotar os tipos das vars.
                var_ptr = self._get_var_ptr(operand_tac, "i32") # Força alocação como i32 se não existir
            else:
                var_ptr = self.var_map[operand_tac]["ptr_llvm"]
            
            loaded_val_reg = self._nova_reg()
            # Assume que todas as variáveis BASIQuinho que são lidas são i32 por enquanto
            self.main_body_instructions.append(f"  {loaded_val_reg} = load i32, i32* {var_ptr}, align 4")
            self.logger.debug(f"LLVM_LOAD_OP: É variável i32 '{operand_tac}', carregada em {loaded_val_reg} de {var_ptr}")
            return "i32", loaded_val_reg

    def gerarCodigoLLVM(self, codigo_tac: list):
        self.logger.info("Iniciando geração de Código LLVM IR...")
        if not codigo_tac and not self.erro_handler.houve_erro_fatal():
             self.logger.info("Código TAC vazio, Geração LLVM produzirá corpo de main vazio.")
        elif not codigo_tac and self.erro_handler.houve_erro_fatal(): 
            self.logger.error("Código TAC não fornecido devido a erros anteriores, Geração LLVM não pode prosseguir.")
            return None
        elif not codigo_tac : 
             self.logger.info("Código TAC vazio (programa fonte pode ser vazio). Geração LLVM produzirá corpo de main mínimo.")

        self.main_body_instructions = []
        self.global_definitions = []
        self.reg_count = 0
        self.var_map = {}
        self.global_str_count = 0
        
        # Instruções de alocação a serem inseridas no início do bloco 'entry'
        alloc_instructions = []

        try:
            for instrucao_tac in codigo_tac:
                self.logger.debug(f"Processando TAC para LLVM: {instrucao_tac}")
                
                comando_ou_destino = ""
                partes_rhs = [] # Para o lado direito de := ou argumento de PRINT/INPUT

                if instrucao_tac.startswith("PRINT "):
                    comando_ou_destino = "PRINT"
                    partes_rhs = [instrucao_tac[len("PRINT "):].strip()]
                elif instrucao_tac.startswith("INPUT "):
                    comando_ou_destino = "INPUT"
                    partes_rhs = [instrucao_tac[len("INPUT "):].strip()]
                elif " := " in instrucao_tac:
                    comando_ou_destino, expressao_str = instrucao_tac.split(" := ", 1)
                    comando_ou_destino = comando_ou_destino.strip() # Este é o destino da atribuição
                    partes_rhs = [expressao_str.strip()] # O RHS completo é o primeiro elemento
                else:
                    self.logger.error(f"Formato de instrução TAC não reconhecido: {instrucao_tac}")
                    self.erro_handler.registrar_erro("Gerador LLVM",0,0,f"Formato TAC irreconhecível: {instrucao_tac}", "LLVM")
                    continue

                if comando_ou_destino == "INPUT":
                    var_nome_miniportugol = partes_rhs[0]
                    # Garante que a variável seja alocada (como i32 por padrão para INPUT)
                    alloc_instr = self._get_var_alloc_instruction(var_nome_miniportugol, "i32")
                    if not alloc_instr.startswith("%ptr"): # Se _get_var_alloc_instruction retornou uma instrução de alocação nova
                        if alloc_instr not in alloc_instructions: alloc_instructions.append(alloc_instr)
                    var_ptr = self.var_map[var_nome_miniportugol]["ptr_llvm"]

                    self.main_body_instructions.append(f"  ; TAC: INPUT {var_nome_miniportugol}")
                    scan_call_reg = self._nova_reg()
                    self.main_body_instructions.append(f"  {scan_call_reg} = call i32 (i8*, ...) @scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str.scan.num.fmt, i64 0, i64 0), i32* {var_ptr})")

                elif comando_ou_destino == "PRINT":
                    val_tac_print = partes_rhs[0]
                    self.main_body_instructions.append(f"  ; TAC: PRINT {val_tac_print}")
                    tipo_llvm_op, val_llvm_op = self._load_operand(val_tac_print)

                    if tipo_llvm_op == "i8*":
                        print_call_reg = self._nova_reg()
                        self.main_body_instructions.append(f"  {print_call_reg} = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.print.str.fmt, i64 0, i64 0), i8* {val_llvm_op})")
                    elif tipo_llvm_op == "i32":
                        print_call_reg = self._nova_reg()
                        self.main_body_instructions.append(f"  {print_call_reg} = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.print.num.fmt, i64 0, i64 0), i32 {val_llvm_op})")
                    else:
                        self.logger.error(f"Tipo de operando desconhecido para PRINT LLVM: {tipo_llvm_op} para valor '{val_tac_print}'")
                        self.erro_handler.registrar_erro("Gerador LLVM",0,0,f"Tipo inválido para PRINT: {tipo_llvm_op}", "LLVM")

                elif " := " in instrucao_tac: # Já tratado pelo split, comando_ou_destino é o LHS
                    destino_tac = comando_ou_destino
                    expressao_direita_str = partes_rhs[0]
                    self.main_body_instructions.append(f"  ; TAC: {destino_tac} := {expressao_direita_str}")
                    
                    # Analisa o lado direito: é "op1 op op2" ou "fonte_unica"?
                    expr_direita_parts = expressao_direita_str.split(' ')
                    
                    if len(expr_direita_parts) == 3 and expr_direita_parts[1] in ['+', '-', '*', '/']:
                        # Operação: destino_tac := op1_tac op_str op2_tac
                        op1_tac, op_str, op2_tac = expr_direita_parts[0], expr_direita_parts[1], expr_direita_parts[2]
                        
                        tipo_op1, val_op1 = self._load_operand(op1_tac)
                        tipo_op2, val_op2 = self._load_operand(op2_tac)

                        if tipo_op1 != "i32" or tipo_op2 != "i32":
                            self.logger.error(f"Operação aritmética com tipos não-i32 ({tipo_op1}, {tipo_op2}) não suportada: {instrucao_tac}")
                            self.erro_handler.registrar_erro("Gerador LLVM",0,0,f"Operação com tipos incompatíveis: {instrucao_tac}", "LLVM")
                            continue

                        llvm_op_keyword = ""
                        if op_str == '+': llvm_op_keyword = "add nsw"
                        elif op_str == '-': llvm_op_keyword = "sub nsw"
                        elif op_str == '*': llvm_op_keyword = "mul nsw"
                        elif op_str == '/': llvm_op_keyword = "sdiv"
                        else: # Nunca deve acontecer devido ao check anterior
                            self.erro_handler.registrar_erro("Gerador LLVM", 0,0, f"Operador TAC '{op_str}' não mapeado para LLVM.", "LLVM"); continue
                        
                        result_reg = f"%{destino_tac}" if destino_tac.startswith("t") else self._nova_reg()
                        self.main_body_instructions.append(f"  {result_reg} = {llvm_op_keyword} i32 {val_op1}, {val_op2}")

                        if not destino_tac.startswith("t"): # Se destino é variável BASIQuinho, faz o store
                            # Garante que a variável de destino seja alocada como i32
                            alloc_instr = self._get_var_alloc_instruction(destino_tac, "i32")
                            if not alloc_instr.startswith("%ptr"): 
                                if alloc_instr not in alloc_instructions: alloc_instructions.append(alloc_instr)
                            destino_ptr = self.var_map[destino_tac]["ptr_llvm"]
                            self.main_body_instructions.append(f"  store i32 {result_reg}, i32* {destino_ptr}, align 4")
                    
                    else: # Atribuição simples: destino_tac := fonte_unica_tac (onde fonte_unica_tac é expressao_direita_str)
                        fonte_tac = expressao_direita_str
                        tipo_llvm_fonte, val_llvm_fonte = self._load_operand(fonte_tac)
                        
                        if destino_tac.startswith("t"): # Destino é temporária tX
                            if tipo_llvm_fonte == "i32":
                                self.main_body_instructions.append(f"  %{destino_tac} = add i32 {val_llvm_fonte}, 0 ; Assign i32 to temp {destino_tac}")
                            elif tipo_llvm_fonte == "i8*": # Ex: t0 := GEP_para_string
                                self.main_body_instructions.append(f"  %{destino_tac} = bitcast i8* {val_llvm_fonte} to i8* ; Assign i8* to temp {destino_tac}")
                            else:
                                self.logger.error(f"Atribuição para temporária de tipo desconhecido {tipo_llvm_fonte} para temp {destino_tac}")
                        else: # Destino é variável BASIQuinho
                            var_type_to_alloca = "i32" if tipo_llvm_fonte == "i32" else "i8*"
                            alloc_instr = self._get_var_alloc_instruction(destino_tac, var_type_to_alloca)
                            if not alloc_instr.startswith("%ptr"):
                                 if alloc_instr not in alloc_instructions: alloc_instructions.append(alloc_instr)
                            destino_ptr = self.var_map[destino_tac]["ptr_llvm"]

                            if self.var_map[destino_tac]["llvm_type_pointed_to"] == "i32" and tipo_llvm_fonte == "i32":
                                self.main_body_instructions.append(f"  store i32 {val_llvm_fonte}, i32* {destino_ptr}, align 4")
                            elif self.var_map[destino_tac]["llvm_type_pointed_to"] == "i8*" and tipo_llvm_fonte == "i8*":
                                self.main_body_instructions.append(f"  store i8* {val_llvm_fonte}, i8** {destino_ptr}, align 8")
                            else:
                                self.logger.error(f"LLVM TYPE MISMATCH: Tentando armazenar {tipo_llvm_fonte} (valor: {val_llvm_fonte}) em variável '{destino_tac}' alocada como {self.var_map[destino_tac]['llvm_type_pointed_to']}*. TAC: {instrucao_tac}")
                                self.erro_handler.registrar_erro("Gerador LLVM",0,0,f"Type mismatch no store para var '{destino_tac}'.", "LLVM")
                else:
                     self.logger.warning(f"Instrução TAC não reconhecida para LLVM: {instrucao_tac}")
        
        except Exception as e:
            self.erro_handler.registrar_erro("Gerador LLVM", 0, 0, f"Erro inesperado e crítico na geração LLVM: {e}", "LLVM")
            self.logger.exception("Detalhes da exceção crítica na geração LLVM:")
            return None

        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")
        informational_header = [
            "; Generated by the BASIQuinho compiler",
            "; BASIQuinho Compiler: https://github.com/edwilsonferreira/BASIQuinho",
            f"; Generated on: {date_str} at {time_str}",
            ";",
            "; To compile this LLVM IR code to an executable:",
            "; 1. Ensure you have Clang installed (or an equivalent LLVM toolchain).",
            "; 2. Run the command:",
            ";    clang your_output_filename.ll -o your_executable_name",
            ";",
            "; Alternatively, using llc (LLVM static compiler) and a C linker (e.g., gcc or clang):",
            "; 1. Generate an object file from LLVM IR:",
            ";    llc -filetype=obj your_output_filename.ll -o your_output_filename.o",
            "; 2. Link the object file to create an executable:",
            ";    clang your_output_filename.o -o your_executable_name",
            ";    (or use gcc: gcc your_output_filename.o -o your_executable_name)",
            ";",""
        ]
        module_setup = [
            "target triple = \"x86_64-pc-linux-gnu\" ; Ajuste conforme sua plataforma alvo","",
            "; Declaracoes de funcoes C externas para I/O",
            "@.str.print.num.fmt = private unnamed_addr constant [4 x i8] c\"%d\\0A\\00\"",
            "@.str.print.str.fmt = private unnamed_addr constant [4 x i8] c\"%s\\0A\\00\"",
            "@.str.scan.num.fmt = private unnamed_addr constant [3 x i8] c\"%d\\00\"",
            "declare i32 @printf(i8* nocapture readonly, ...) nounwind",
            "declare i32 @scanf(i8* nocapture readonly, ...) nounwind",""
        ]
        define_main = ["define i32 @main() {","entry:"]
        footer = ["  ret i32 0","}",""]

        # Insere as instruções de alocação após 'entry:'
        final_main_body = alloc_instructions + self.main_body_instructions

        self.codigo_llvm_linhas = (informational_header + module_setup + 
                                   self.global_definitions + 
                                   ([""] if self.global_definitions else []) +
                                   define_main + 
                                   final_main_body + 
                                   footer)
        
        if not self.erro_handler.tem_erros_llvm:
            self.logger.info("Geração de Código LLVM IR concluída.")
            final_code = "\n".join(self.codigo_llvm_linhas)
            self.logger.info("--- Código LLVM IR Gerado (trecho inicial) ---")
            for i, line_llvm in enumerate(self.codigo_llvm_linhas[:30]):
                 self.logger.info(line_llvm)
            if len(self.codigo_llvm_linhas) > 30: self.logger.info("   (...)")
            self.logger.info("------------------------------------------")
            return final_code
        else:
            self.logger.error("Geração de LLVM IR encontrou erros.")
            return None
