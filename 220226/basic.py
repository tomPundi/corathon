from ast import Call, Num
from distutils.log import error
from hashlib import new
from lib2to3.pgen2 import token
from tkinter import N, NONE
from unittest import result
from strings_with_arrows import * 
import string
# CONSTANT

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

# ERROR
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}:{self.details}\n'
        result += f'File {self.pos_start.fileName}, line {self.pos_start.ln + 1}'
        # 下面一行是直接复制他的实现方法，可以后续看
        result += '\n\n' + string_with_arrows(self.pos_start.fileTxt, self.pos_start, self.pos_end)

        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class IllegalSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Illegal Syntax', details)

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}:{self.details}\n'
        result += '\n\n' + string_with_arrows(self.pos_start.fileTxt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.context
        
        while ctx:
            result = f'File {pos.fileName}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            # print("result", result)
            pos = ctx.parent_entry_pos
            ctx = ctx.parent
        
        return 'Traceback (most recent call last):\n' + result

# POSITION
class Position:
    def __init__(self, idx, ln, col, fileName, fileTxt):
        self.idx = idx
        self.ln = ln 
        self.col = col
        self.fileName = fileName
        self.fileTxt = fileTxt
    
    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.idx = 0
            self.col = 0
        
        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fileName, self.fileTxt)
        

# TOKEN 
TT_LSQUARE    = 'LSQUARE'
TT_RSQUARE    = 'RSQUARE'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD    = 'KEYWORD'
TT_EQ         = 'EQ'
TT_INT    = 'INT'
TT_FLOAT  = 'FLOAT'
TT_STRING = 'STRING'
TT_PLUS   = 'PLUS'
TT_MINUS  = 'MINUS'
TT_MUL    = 'MUL'
TT_DIV    = 'DIV'
TT_POW    = 'POW'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_EOF    = 'EOF'
TT_EE     = 'EE'
TT_NE     = 'NQ'
TT_LT     = 'LT'
TT_GT     = 'GT'
TT_LTE    = 'LTE'
TT_GTE    = 'GTE'
TT_COMMA  = 'COMMA'
TT_ARROW  = 'ARROW'



KEYWORDS = [
    'var',
    'and',
    'or',
    'not',
    'if',
    'then',
    'elif',
    'else',
    'for',
    'to',
    'step',
    'while',
    'fun'
]


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

    def matches(self, type_, value):
        return self.type == type_ and self.value == value 


# LEXER
class Lexer:
    # 注意这里修改了顺序
    def __init__(self, fileName, text):
        self.fileName = fileName
        self.text = text
        self.pos = Position(-1, 0, -1, fileName, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
        # print("self.current_char now", self.current_char)

    def make_tokens(self):
        tokens = []
        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                # print("self.current_char", self.current_char)
                # print("tokens", tokens)
                tokens.append(self.make_numbers())
                # print("self.current_char", self.current_char)
                # print("tokens", tokens)
            elif  self.current_char in LETTERS:
                tokens.append(self.make_identifiers())
            elif  self.current_char == '"':
                tokens.append(self.make_strings())
            elif  self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '-':
                # tokens.append(Token(TT_MINUS, pos_start=self.pos))
                # self.advance()
                tokens.append(self.make_minus_or_arrow()) # function have 2 expression like '-' or '->'
                # self.advance()
            elif  self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif  self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif  self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif  self.current_char == '!':
                tok, error = self.make_not_equals()
                if error: return [], error
                tokens.append(tok)
            elif  self.current_char == '=':
                tokens.append(self.make_equals())
            elif  self.current_char == '<':
                tokens.append(self.make_less_than())
            elif  self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif  self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, '!' + char + '!')
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_numbers(self):
        num_str = ''
        dot_count = 0 
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break 
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)




    def make_strings(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()

        escape_characters = {
            'n': '\n',
            't': '\t'
        }

        while self.current_char != None and (self.current_char != '"' or escape_character):
            if self.current_char == '\\':
                string += escape_characters.get(self.current_char, self.current_char)
            else: 
                string += self.current_char
            self.advance()

        self.advance()
        return Token(TT_STRING, string, pos_start, self.pos)




    def make_identifiers(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()
        
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        # print('tok_type', tok_type, 'id_str', id_str)
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_minus_or_arrow(self):
        tok_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '>':
            self.advance()
            tok_type = TT_ARROW
        
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None
        
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self):
        tok_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    
    def make_less_than(self):
        tok_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_greater_than(self):
        tok_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

# NODES
class NumberNode:
    def __init__(self,tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class StringNode:
    def __init__(self,tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'{self.element_nodes}'

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end
        
class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end
    
    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node 
        self.pos_start = self.op_tok.pos_start
        # 这一步待了解
        self.pos_end = node.pos_end
    
    def __repr__(self):
        return f'({self.op_tok}, {self.node})'
        
class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end

class ForNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end

class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end

class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end
        



# PARSER RESULT
# 再次抽象代替广义的node
class ParserResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
    
    def register_advance(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node 

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self


# PARSER
class Parser:
    # the video is 1 so the parser should be changed
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    # parse
    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            res.failure(IllegalSyntaxError(
            # tok.pos_start, tok.pos_end, "Expect INT or FLOAT!"
            self.current_tok.pos_start, self.current_tok.pos_end, 
			"Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
        ))
        return res

    def if_expr(self):
        res = ParserResult()
        cases = []
        else_case = None 

        if not self.current_tok.matches(TT_KEYWORD, 'if'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'if'"
				))  

        res.register_advance()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'then'"
				))  

        res.register_advance()
        self.advance()

        expr = res.register(self.expr())
        if res.error: return res
        cases.append((condition, expr))

        while self.current_tok.matches(TT_KEYWORD, 'elif'):
            res.register_advance()
            self.advance()

            condition = res.register(self.expr())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'then'"
				)) 
            res.register_advance()
            self.advance() 

            expr = res.register(self.expr())
            if res.error: return res
            cases.append((condition, expr))

        if self.current_tok.matches(TT_KEYWORD, 'else'):
            res.register_advance()
            self.advance()

            else_case = res.register(self.expr())
            if res.error: return res

        return res.success(IfNode(cases, else_case))

    def for_expr(self):
        res = ParserResult()

        if not self.current_tok.matches(TT_KEYWORD, 'for'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'for'"
				))  
        res.register_advance()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier"
				))  
        var_name = self.current_tok
        res.register_advance()
        self.advance()

        if self.current_tok.type != TT_EQ:
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '='"
				))
        res.register_advance()
        self.advance()
        start_value = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'to'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'to'"
				))  
        res.register_advance()
        self.advance()
        end_value = res.register(self.expr())
        if res.error: return res

        if self.current_tok.matches(TT_KEYWORD, 'step'):
            res.register_advance()
            self.advance()
            step_value = res.register(self.expr())
            if res.error: return res
        else:
            step_value = None 

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(IllegalSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            )) 
        res.register_advance()
        self.advance()
        body = res.register(self.expr())
        if res.error: return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body))


    def while_expr(self):
        res = ParserResult()

        if not self.current_tok.matches(TT_KEYWORD, 'while'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'while'"
				))  
        res.register_advance()
        self.advance()
        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'then'"
				))  
        res.register_advance()
        self.advance()
        body = res.register(self.expr())
        if res.error: return res

        return res.success(WhileNode(condition, body))


    def fun_def(self):
        res = ParserResult()
        if not self.current_tok.matches(TT_KEYWORD, 'fun'):
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected 'fun'"
				))  
        res.register_advance()
        self.advance()

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advance()
            self.advance()
            if self.current_tok.type != TT_LPAREN:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '('"
				))
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '('"
				))
        res.register_advance()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advance()
            self.advance()

            while self.current_tok.type == TT_COMMA:
                res.register_advance()
                self.advance()
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(IllegalSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier"
                    ))
                arg_name_toks.append(self.current_tok)
                res.register_advance()
                self.advance()
            
            if self.current_tok.type != TT_RPAREN:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ',' or ')'"
				))
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier or ')'"
				))
        res.register_advance()
        self.advance()

        if self.current_tok.type != TT_ARROW:
            return res.failure(IllegalSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '->'" 
            ))
        res.register_advance()
        self.advance()
        node_to_return = res.register(self.expr())
        if res.error: return res 

        return res.success(FuncDefNode(
            var_name_tok,
            arg_name_toks,
            node_to_return
        ))


    def list_expr(self):
        res = ParserResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(IllegalSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '['" 
            ))
        
        res.register_advance()
        self.advance()

        if self.current_tok.type == TT_RSQUARE:
            res.register_advance()
            self.advance()
        else: 
            element_nodes.append(res.register(self.expr()))
            if res.error: 
                return res.failure(IllegalSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'var', 'and', 'or', 'not', 'if', 'then', 'elif', 'else', 'for', 'to', 'step', 'while', 'fun'"
                ))
            while self.current_tok.type == TT_COMMA:
                res.register_advance()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error: return res 
            
            if self.current_tok.type != TT_RSQUARE:
                return res.failure(IllegalSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ',' or ']'"
                ))
                
            res.register_advance()
            self.advance()

        return res.success(ListNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))


    def atom(self):
        res = ParserResult()
        tok = self.current_tok
        if tok.type in (TT_INT, TT_FLOAT): 
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            return res.success(NumberNode(tok))

        if tok.type == TT_STRING:
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            return res.success(StringNode(tok))
        elif tok.type == TT_IDENTIFIER:
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            return res.success(VarAccessNode(tok))
        elif tok.type == TT_LSQUARE:
            # res.register(self.advance())
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)
        elif tok.type == TT_LPAREN:
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == TT_RPAREN:
                # res.register(self.advance())
                res.register_advance()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ')'"
				))
        elif tok.matches(TT_KEYWORD, 'if'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)
        elif tok.matches(TT_KEYWORD, 'for'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)
        elif tok.matches(TT_KEYWORD, 'while'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)
        elif tok.matches(TT_KEYWORD, 'fun'):
            fun_def = res.register(self.fun_def())
            if res.error: return res
            return res.success(fun_def)

        return res.failure(IllegalSyntaxError(
            tok.pos_start, tok.pos_end, "Expect INT, FLOAT, IDENTIFIER, '+', '-', '(', '[', 'if', 'for', 'while' or 'fun'!"
        ))


    def call(self):
        res = ParserResult()
        atom = res.register(self.atom())
        if res.error: return res 

        if self.current_tok.type == TT_LPAREN:
            res.register_advance()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                res.register_advance()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error: 
                    return res.failure(IllegalSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'var', 'and', 'or', 'not', 'if', 'then', 'elif', 'else', 'for', 'to', 'step', 'while', 'fun'"
                    ))
                while self.current_tok.type == TT_COMMA:
                    res.register_advance()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res 
                
                if self.current_tok.type != TT_RPAREN:
                    return res.failure(IllegalSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')'"
				    ))
                
                res.register_advance()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)



    def power(self):
        return self.bin_op(self.call, (TT_POW, ), self.factor)
    
    def factor(self):
        res = ParserResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res 
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    # 后续实现后有一次抽象
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def comp_expr(self):
        res = ParserResult()

        if self.current_tok.matches(TT_KEYWORD, 'not'):
            op_tok = self.current_tok
            res.register_advance()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res 
            return res.success(UnaryOpNode(op_tok, node))
        
        node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

        if res.error:
            return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expect 'var', INT, FLOAT, IDENTIFIER, '+', '-' or '(', '[', 'NOT'!"
				))
        
        return res.success(node)

    def expr(self):
        res = ParserResult()

        if self.current_tok.matches(TT_KEYWORD, 'var'):
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier"
				))
            var_name = self.current_tok
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            if self.current_tok.type != TT_EQ:
                return res.failure(IllegalSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '='"
				))
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or')))) 
        if res.error: 
            return res.failure(IllegalSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end, 
            "Expect 'var', INT, FLOAT, IDENTIFIER, '+', '-', '(', '[', 'if', 'for', 'while' or 'fun'!"
        ))
        return res.success(node)

    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a

        res = ParserResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            # res.register(self.advance())
            res.register_advance()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)
        
        return res.success(left)


# RUNTIME RESULT
# 主要是用来不间断查找内容
class RTResult:
    def __init__(self):
        self.value = None
        self.error = None
    
    def register(self, res):
        if res.error: self.error = res.error
        return res.value
    
    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


# VALUES
class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()
    
    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end 
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add_to(self, other):
        return None, self.illegal_operation(other)

    def sub_by(self, other):
        return None, self.illegal_operation(other)

    def mul_by(self, other):
        return None, self.illegal_operation(other)

    def div_by(self, other):
        return None, self.illegal_operation(other)

    def pow_by(self, other):
        return None, self.illegal_operation(other)

    def get_ee(self, other):
        return None, self.illegal_operation(other)

    def get_ne(self, other):
        return None, self.illegal_operation(other)

    def get_lt(self, other):
        return None, self.illegal_operation(other)

    def get_gt(self, other):
        return None, self.illegal_operation(other)

    def get_lte(self, other):
        return None, self.illegal_operation(other)

    def get_gte(self, other):
        return None, self.illegal_operation(other)

    def and_by(self, other):
        return None, self.illegal_operation(other)

    def or_by(self, other):
        return None, self.illegal_operation(other)

    def not_by(self):
        return None, self.illegal_operation(other)

    def execute(self, args):
        # return None, self.illegal_operation()
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if not other: other = self
        return RTError(
            self.pos_start, other.pos_end,
            'Illegal operation',
            self.context
        )


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def add_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def sub_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def mul_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def div_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Division by zero',
                    self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def pow_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_ee(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def get_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def and_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def or_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def not_by(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value != 0

    def __repr__(self):
        return str(self.value)

class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def add_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def mul_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value > 0

    def __repr__(self):
        return f'"{self.value}"'

class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def add_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def sub_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Element at this index could not be removed from list because index is out of bounds!',
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def mul_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)

    def div_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Element at this index could not be retrieved from list because index is out of bounds!',
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = List(self.elements[:])
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'[{",".join([str(x) for x in self.elements])}]'

class Function(Value):
    def __init__(self, name, body_node, arg_names):
        super().__init__()
        self.name = name or '<anonymous>'
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

        if len(args) > len(self.arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(self.arg_names)} too many args passed into '{self.name}'!",
                self.context
            ))

        if len(args) < len(self.arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(self.arg_names) - len(args)} too few args passed into '{self.name}'!",
                self.context
            ))

        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_value = args[i]
            arg_value.set_context(new_context)
            new_context.symbol_table.set(arg_name, arg_value)

        value = res.register(interpreter.visit(self.body_node, new_context))
        if res.error: return res
        return res.success(value)

    def copy(self):
        copy  = Function(self.name, self.body_node, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy 
    
    def __repr__(self):
        return f"<function {self.name}>"

# CONTEXT
class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


# SYMBOL TABLE
class SymbolTable:
    def __init__(self, parent_=None):
        self.symbols = {}
        self.parent = parent_
        print("self.parent now!!!", self.parent)

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value 
        
    def set(self, name, value):
        print("self, name, value now!!!", self, name, value)
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


# INTERPRETER
class Interpreter:
    def visit(self, node, context):
        # print('node and context now!!!!!!!!!!', node, context)
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        # print('method_name and method now!!!!!!!!!!', method_name, method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')
    
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))
        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return res.success(value)

 
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error: return res

        context.symbol_table.set(var_name, value)
        return res.success(value)


    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.error: return res 

        return RTResult().success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_BinOpNode(self, node, context):
        res = RTResult()

        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_tok.type == TT_PLUS:
            result, error = left.add_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.sub_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.mul_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.div_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.pow_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = left.get_ee(right)
        elif node.op_tok.type == TT_NE:
            result, error = left.get_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = left.get_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = left.get_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = left.get_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = left.get_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, 'and'):
            result, error = left.and_by(right)
        elif node.op_tok.matches(TT_KEYWORD, 'or'):
            result, error = left.or_by(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        # print("Found unary op node!")
        number = res.register(self.visit(node.node, context))

        error = None
        if node.op_tok.type == TT_MINUS:
            number, error = number.mul_by(Number(-1))
        elif node.op_tok.matches(TT_KEYWORD, 'not'):
            number, error = number.not_by()
        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node, context):
        res = RTResult()

        for condition, expr in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.error: return res

            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.error: return res
                return res.success(expr_value)
        
        if node.else_case:
            else_value = res.register(self.visit(node.else_case, context))
            if res.error: return res
            return res.success(else_value)
        
        return res.success(None)


    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.error: return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.error: return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.error: return res
        else:
            step_value = Number(1)

        i = start_value.value
        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value 
            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )


    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.error: return res
            # print('condition now!!!!!!!!!', condition)


            if not condition.is_true(): break

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res
            # print('res now!!!!!!!!!', res)

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FuncDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = Function(func_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)

        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)
        
        return res.success(func_value)

    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error: return res 
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error: return res 
        
        return_value = res.register(value_to_call.execute(args))
        if res.error: return res 
        return res.success(return_value)

global_symbol_table = SymbolTable()
print("global_symbol_table now!!!", global_symbol_table)
print("global_symbol_table.set now!!!", global_symbol_table.set)
global_symbol_table.set('null', Number(0))
global_symbol_table.set('true', Number(1))
global_symbol_table.set('false', Number(0))


def run(fileName, text):
    #  Generate tokens
    lex = Lexer(fileName, text)
    tokens, error = lex.make_tokens()
    if error: return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run program
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error