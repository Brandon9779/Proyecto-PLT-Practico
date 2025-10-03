# -*- coding: utf-8 -*-
import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'lexeme', 'line', 'col'])

class SnakeLexer(object):
    def __init__(self, code):
        self.code = code
        self.line_num = 1
        self.line_start = 0

        # -----------------------------
        # Definición de tokens (regex)
        # -----------------------------
        token_spec = [
            ('NUMBER',    r'\d+(?:\.\d+)?'),          # Números int/float
            ('STRING',    r'"[^"\r\n]*"'),            # "texto"
            ('BOOLEAN',   r'\b(?:true|false)\b'),     # true/false
            ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'), # Identificadores
            ('LBRACE',    r'\{'),                     # {
            ('RBRACE',    r'\}'),                     # }
            ('LBRACKET',  r'\['),                     # [
            ('RBRACKET',  r'\]'),                     # ]
            ('LPAREN',    r'\('),                     # (
            ('RPAREN',    r'\)'),                     # )
            ('EQUAL',     r'='),                      # =
            ('COLON',     r':'),                      # :
            ('COMMA',     r','),                      # ,
            ('SEMI',      r';'),                      # ;
            ('NEWLINE',   r'\n'),                     # fin de línea
            ('SKIP',      r'[ \t\r]+'),               # espacios/tabs
            ('COMMENT',   r'//[^\n]*|#[^\n]*'),       # comentarios
            ('MISMATCH',  r'.'),                      # otro (error)
        ]
        self.tok_regex = re.compile('|'.join('(?P<%s>%s)' % p for p in token_spec))

        # -----------------------------
        # Keywords del DSL (Snake)
        # -----------------------------
        self.keywords = {
            # encabezado
            'game', 'juego', 'title', 'author', 'version',
            # secciones
            'tablero', 'serpiente', 'comida', 'paredes', 'perdiste',
            'reglas', 'puntos', 'velocidad', 'controles', 'hud',
            'assets', 'audio', 'movimientos_permitidos', 'niveles',
            # tablero
            'filas', 'columnas', 'fondo', 'celda_px', 'inicio_lleno', 'bordes_solidos',
            # serpiente
            'velocidad_cps', 'largo_inicial', 'crecimiento_por_comida',
            'color', 'posicion_inicial', 'direccion_inicial', 'x', 'y',
            'colores_segmentos', 'cola_elastica',
            # comida
            'max_activa', 'items', 'tipo', 'valor_puntos', 'respawn_ms',
            'evitar_sobre_serpiente', 'evitar_paredes',
            # paredes
            'usar_paredes', 'lista',
            # derrota / reglas
            'colision_pared', 'colision_cuerpo', 'salir_tablero', 'tiempo_agotado',
            'wrap_edges', 'tick_ms', 'pausa_permitida',
            # puntuación
            'puntos_iniciales', 'ganar_puntos', 'perder_puntos',
            'bonus_longitud_activo', 'bonus_longitud_cada_segmentos', 'bonus_longitud_valor',
            'combo_tiempo_activo', 'combo_tiempo_ventana_ms', 'combo_tiempo_bonus',
            'multiplicadores', 'racha_sin_choques_activo', 'racha_umbral', 'racha_factor',
            # velocidad / progresión
            'velocidad_inicial_cps', 'velocidad_progresiva',
            'aumentar_velocidad', 'cada_puntos', 'factor_aumento', 'limite_cps',
            'control', 'mantener_tick_constante', 'input_buffer_ms',
            # niveles
            'id', 'objetivo_puntos', 'cps_min', 'cps_max', 'paredes_extra',
            # controles
            'arriba', 'abajo', 'izquierda', 'derecha', 'pausar', 'reiniciar',
            # HUD
            'mostrar_puntaje', 'mostrar_velocidad', 'mostrar_nivel', 'posiciones',
            'puntaje_x', 'puntaje_y', 'velocidad_x', 'velocidad_y', 'nivel_x', 'nivel_y',
            # assets / colores
            'charset', 'simbolos', 'cabeza', 'pared', 'fondo', 'paleta',
            'verde', 'verde_oscuro', 'rojo', 'amarillo', 'morado', 'negro', 'blanco',
            # audio
            'habilitado', 'sonidos', 'comer', 'chocar', 'subir_nivel', 'volumen_global'
        }

    def tokenize(self):
        tokens = []
        col = 1  # por si el archivo está vacío
        for mo in self.tok_regex.finditer(self.code):
            kind = mo.lastgroup
            lexeme = mo.group()
            col = mo.start() - self.line_start + 1

            if kind == 'NEWLINE':
                self.line_num += 1
                self.line_start = mo.end()
                continue
            if kind in ('SKIP', 'COMMENT'):
                continue

            if kind == 'STRING':
                tokens.append(Token('STRING', lexeme[1:-1], self.line_num, col))
                continue
            if kind == 'NUMBER':
                val = float(lexeme) if '.' in lexeme else int(lexeme)
                tokens.append(Token('NUMBER', val, self.line_num, col))
                continue
            if kind == 'BOOLEAN':
                tokens.append(Token('BOOL', lexeme == 'true', self.line_num, col))
                continue

            if kind == 'ID':
                # GAME especial: 'game' o 'juego'
                if lexeme in ('game', 'juego'):
                    tokens.append(Token('GAME', lexeme, self.line_num, col))
                elif lexeme in self.keywords:
                    tokens.append(Token(lexeme.upper(), lexeme, self.line_num, col))
                else:
                    tokens.append(Token('ID', lexeme, self.line_num, col))
                continue

            if kind == 'MISMATCH':
                raise RuntimeError("Caracter inesperado %r en línea %d, col %d"
                                   % (lexeme, self.line_num, col))

            # símbolos y resto
            tokens.append(Token(kind, lexeme, self.line_num, col))

        tokens.append(Token('EOF', '', self.line_num, col))
        return tokens


if __name__ == '__main__':
    # Ejemplo de uso estilo Py2
    with open("snake.brik", "r") as f:
        code = f.read()
    lexer = SnakeLexer(code)
    for t in lexer.tokenize():
        print t
