import re 
import sys
import json
from collections import namedtuple

Token = namedtuple('Token', ['type', 'lexeme', 'line', 'col'])


class Node(object):
    def to_dict(self):
        result = {'type': self.__class__.__name__}
        for k, v in self.__dict__.items():
            if isinstance(v, list):
                result[k] = [i.to_dict() if isinstance(i, Node) else i for i in v]
            elif isinstance(v, Node):
                result[k] = v.to_dict()
            else:
                result[k] = v
        return result

class GameNode(Node):
    def __init__(self, name, body): 
        self.name = name
        self.body = body

class BlockNode(Node):
    def __init__(self, name): 
        self.name = name
        self.statements = []

class AssignNode(Node):
    def __init__(self, key, value): 
        self.key= key
        self.value = value

class ListNode(Node):
    def __init__(self, items): 
        self.items = items

class ObjectNode:
    def __init__(self, pairs):
        self.pairs = pairs
    def __repr__(self):
        return f"ObjectNode({self.pairs})"
    def to_dict(self):
        return {k: (v.to_dict() if hasattr(v, 'to_dict') else v) for k, v in self.pairs}

class FunctionNode(Node):
    def __init__(self, name, args): 
        self.name= name
        self.args = args
        
class ValueNode(Node):
    def __init__(self, value): 
        self.value = value



#   LEXER

class GameLexer(object):
    def __init__(self, code):
        self.code = code
        self.line_num = 1
        self.line_start = 0
        self.errors = []

        self.keywords = {
            'juego', 'game', 'tablero', 'piezas', 'puntos', 'velocidad', 'controles', 'perdiste',
            'filas', 'columnas', 'fondo', 'inicio_lleno', 'color', 'rotaciones',
            'random', 'true', 'false',
            'pieza_inicial', 'pieza_siguiente', 'ganar_puntos', 'eliminar_fila',
            'velocidad_progresiva', 'aumentar_velocidad', 'cada_puntos', 'cantidad_aumento',
            'izquierda', 'derecha', 'caida', 'rotar', 'pausar',
            'I', 'O', 'T', 'L', 'J', 'S', 'Z',
            'serpiente', 'comida', 'paredes', 'reglas', 'assets', 'title', 'author', 'version',
            'velocidad_cps', 'largo_inicial', 'crecimiento_por_comida', 'posicion_inicial',
            'direccion_inicial', 'max_activa', 'items', 'tipo', 'valor_puntos', 'respawn_ms',
            'evitar_sobre_serpiente', 'evitar_paredes', 'usar_paredes', 'lista',
            'colision_pared', 'colision_cuerpo', 'salir_tablero', 'wrap_edges', 'tick_ms',
            'bonus_longitud_activo', 'bonus_longitud_cada_segmentos', 'bonus_longitud_valor',
            'velocidad_inicial_cps', 'factor_aumento', 'limite_cps',
            'arriba', 'abajo', 'serpiente', 'cabeza', 'comida', 'pared', 'simbolos', 'charset'
        }

        token_specification = [
            ('NUMBER',   r'\d+(\.\d+)?'),
            ('STRING',   r'"(\\.|[^"])*"'),
            ('BOOLEAN',  r'\b(true|false)\b'),
            ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
            ('LBRACE',   r'\{'), 
            ('RBRACE',   r'\}'),
            ('LBRACKET', r'\['), 
            ('RBRACKET', r'\]'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('EQUAL',    r'='), 
            ('COMMA',    r','), 
            ('SEMICOLON',r';'),
            ('COLON', r':'),
            ('COMMENT', r'##.*|#.*'),
            ('NEWLINE',  r'\n'),
            ('SKIP',     r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]

        self.tok_regex = re.compile('|'.join('(?P<%s>%s)' % pair for pair in token_specification))

    def tokenize(self):
        tokens = []
        col = 1
        for mo in self.tok_regex.finditer(self.code):
            kind = mo.lastgroup
            lexeme = mo.group()
            col = mo.start() - self.line_start + 1

            if kind == 'NUMBER':
                pass
            elif kind == 'STRING':
                pass
            elif kind == 'BOOLEAN':
                pass
            elif kind == 'ID':
                if lexeme in self.keywords:
                    kind = lexeme.upper()
            elif kind == 'NEWLINE':
                self.line_num += 1
                self.line_start = mo.end()
                continue
            elif kind in ('SKIP', 'COMMENT'):
                continue
            elif kind == 'MISMATCH':
                self.errors.append("⚠️ Error léxico: carácter inesperado '%s' en línea %d, col %d" %
                                   (lexeme, self.line_num, col))
                continue

            tokens.append(Token(kind, lexeme, self.line_num, col))
        tokens.append(Token('EOF', '', self.line_num, col))
        return tokens


#       PARSER

class ParserError(Exception): 
    pass

class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.errors = []

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def expect(self, token_type):
        if self.current_token is None:
            self.errors.append("❌ Error sintáctico: se esperaba '%s' pero se llegó al final" % token_type)
            raise ParserError
        if self.current_token.type != token_type:
            self.errors.append(
                "❌ Error sintáctico en línea %d, col %d: se esperaba '%s' pero se encontró '%s'" %
                (self.current_token.line, self.current_token.col, token_type, self.current_token.lexeme)
            )
            raise ParserError
        self.advance()

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None


    def parse(self):
        try:
            return self.parse_game()
        except ParserError:
            return None

    def parse_game(self):
        if self.current_token.type not in ('GAME', 'JUEGO'):
            self.errors.append("❌ El archivo debe comenzar con 'game' o 'juego'")
            raise ParserError
        self.advance()

        name = None
        if self.current_token and self.current_token.type in ('STRING', 'ID'):
            name = self.current_token.lexeme.strip('"')
            self.advance()

        self.expect('LBRACE')
        body = self.parse_block()
        self.expect('RBRACE')

        return GameNode(name, body)


    def parse_block(self):
        block = BlockNode("block")
        while self.current_token and self.current_token.type not in ('RBRACE', 'EOF'):
            if self.current_token.type == 'ID' or self.current_token.type.isupper():
                key = self.current_token.lexeme
                self.advance()

                if self.current_token and self.current_token.type == 'EQUAL':
                    self.advance()
                    value = self.parse_value()
                    node = AssignNode(key, value)
                    block.statements.append(node)
                    if self.current_token and self.current_token.type == 'SEMICOLON':
                        self.advance()
                elif self.current_token and self.current_token.type == 'LBRACE':
                    self.advance()
                    subblock = self.parse_block()
                    subblock.name = key
                    block.statements.append(subblock)
                    self.expect('RBRACE')
                else:
                    self.errors.append(
                        "⚠️ Error sintáctico: se esperaba '=' o '{' después de '%s' (línea %d, col %d)" %
                        (key, self.current_token.line, self.current_token.col)
                    )
                    self.advance()
            else:
                self.advance()
        return block

    def parse_value(self):
        tok = self.current_token
        if tok is None:
            self.errors.append("⚠️ Valor inesperado: fin de entrada")
            raise ParserError
        if tok.type == 'NUMBER':
            value = ValueNode(float(tok.lexeme) if '.' in tok.lexeme else int(tok.lexeme))
            self.advance()
            return value
        elif tok.type == 'STRING':
            value = ValueNode(tok.lexeme.strip('"'))
            self.advance()
            return value
        elif tok.type == 'BOOLEAN':
            value = ValueNode(True if tok.lexeme == 'true' else False)
            self.advance()
            return value
        elif tok.type == 'LBRACKET':
            return self.parse_list()
        elif tok.type == 'LBRACE':
            return self.parse_object()
        elif tok.type == 'ID' or tok.type.isupper():
            if self.peek() and self.peek().type == 'LPAREN':
                return self.parse_function()
            else:
                value = ValueNode(tok.lexeme)
                self.advance()
                return value
        else:
            self.errors.append("⚠️ Valor inesperado '%s' en línea %d, col %d" %
                           (tok.lexeme, tok.line, tok.col))
            self.advance()
            return ValueNode(tok.lexeme)

    def parse_list(self):
        self.expect('LBRACKET')
        elements = []
        while self.current_token and self.current_token.type != 'RBRACKET':
            elements.append(self.parse_value())
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
        self.expect('RBRACKET')
        return ListNode(elements)
    
    def parse_object(self):
        """Parses { key: value, key2: value2 }"""
        self.expect('LBRACE')
        pairs = []
        while self.current_token and self.current_token.type != 'RBRACE':
            key = self.current_token.lexeme
            self.expect('ID')              
            self.expect('COLON')
            value = self.parse_value()     
            pairs.append((key, value))
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
        self.expect('RBRACE')
        return ObjectNode(pairs)

    def parse_function(self):
        name = self.current_token.lexeme
        self.advance()           
        self.expect('LPAREN')
        args = []
        while self.current_token and self.current_token.type != 'RPAREN':
            args.append(self.parse_value())
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
            # prevención por si hay error y current_token queda None
            if self.current_token is None:
                self.errors.append("❌ Error sintáctico: paréntesis no cerrado en llamada a '%s'" % name)
                raise ParserError
        self.expect('RPAREN')
        return FunctionNode(name, args)



if __name__ == '__main__':
    with open('Tetris.txt', 'r') as f:
        code = f.read()

    lexer = GameLexer(code)
    tokens = lexer.tokenize()

    if lexer.errors:
        print("=== ERRORES LÉXICOS ===")
        for e in lexer.errors:
            print(e)
        print("========================\n")

    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors:
        print("=== ERRORES SINTÁCTICOS ===")
        for e in parser.errors:
            print(e)
        print("============================\n")

    if ast:
        print("=== ÁRBOL SINTÁCTICO ===")
        print(json.dumps(ast.to_dict(), indent=2))
