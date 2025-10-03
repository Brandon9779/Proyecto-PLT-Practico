
import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'lexeme', 'line', 'col'])

class TetrisLexer(object):
    def __init__(self, code):
        self.code = code
        self.line_num = 1
        self.line_start = 0

        # Definición de tokens usando regex
        token_specification = [
            ('NUMBER',   r'\d+(\.\d+)?'),             # Números enteros y decimales
            ('STRING',   r'"(\\.|[^"])*"'),           # Strings entre comillas
            ('BOOLEAN',  r'\b(true|false)\b'),        # Booleanos
            ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),  # Identificadores
            ('LBRACE',   r'\{'),                      # {
            ('RBRACE',   r'\}'),                      # }
            ('LBRACKET', r'\['),                      # [
            ('RBRACKET', r'\]'),                      # ]
            ('LPAREN',   r'\('),                      # (
            ('RPAREN',   r'\)'),                      # )
            ('EQUAL',    r'='),                       # =
            ('COMMA',    r','),                       # ,
            ('NEWLINE',  r'\n'),                      # saltos de línea
            ('SKIP',     r'[ \t]+'),                  # espacios y tabs
            ('COMMENT',  r'\#.*'),                    # comentarios con #
            ('MISMATCH', r'.'),                       # cualquier otro (error)
        ]

        # Regex maestro
        self.tok_regex = re.compile('|'.join(
            '(?P<%s>%s)' % pair for pair in token_specification
        ))

        # Palabras clave estrictas del DSL (lo demás será ID flexible)
        self.keywords = {
            'juego', 'tablero', 'piezas', 'rotaciones',
            'perdiste', 'eliminacion_filas', 'puntos',
            'velocidad', 'controles', 'random'
        }

    def tokenize(self):
        tokens = []
        for mo in self.tok_regex.finditer(self.code):
            kind = mo.lastgroup
            lexeme = mo.group()
            col = mo.start() - self.line_start + 1

            if kind == 'NUMBER':
                kind = 'NUMBER'
            elif kind == 'STRING':
                kind = 'STRING'
            elif kind == 'BOOLEAN':
                kind = 'BOOLEAN'
            elif kind == 'ID':
                # Solo algunas palabras reservadas pasan a mayúscula
                if lexeme in self.keywords:
                    kind = lexeme.upper()
                else:
                    kind = 'ID'   # identificador libre permitido
            elif kind == 'NEWLINE':
                self.line_num += 1
                self.line_start = mo.end()
                continue
            elif kind in ('SKIP', 'COMMENT'):
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError("Caracter inesperado %r en línea %d" % (lexeme, self.line_num))

            tokens.append(Token(kind, lexeme, self.line_num, col))

        tokens.append(Token('EOF', '', self.line_num, col))
        return tokens


if __name__ == '__main__':
    with open("Tetris.txt", "r") as f:
        code = f.read()

    lexer = TetrisLexer(code)
    for t in lexer.tokenize():
        print t
