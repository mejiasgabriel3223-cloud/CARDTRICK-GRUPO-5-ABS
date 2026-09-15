import pygame


class Boton:
    """Botón reutilizable para pantallas del menú y configuración."""

    def __init__(
        self,
        x,
        y,
        w,
        h,
        texto,
        color_normal=(60, 75, 90),
        color_hover=(95, 120, 150),
        color_texto=(255, 255, 255),
        font_size=24,
        radio=12,
        accion=None,
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.texto = texto
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.color_texto = color_texto
        self.fuente = pygame.font.SysFont("Arial", font_size, bold=True)
        self.radio = radio
        self.accion = accion

    def set_texto(self, texto):
        self.texto = texto

    def manejar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect.collidepoint(evento.pos):
                return self.accion
        return None

    def dibujar(self, pantalla, mouse_pos=None):
        hover = mouse_pos is not None and self.rect.collidepoint(mouse_pos)
        color = self.color_hover if hover else self.color_normal

        pygame.draw.rect(pantalla, (20, 20, 24), self.rect.inflate(6, 6), border_radius=self.radio + 2)
        pygame.draw.rect(pantalla, color, self.rect, border_radius=self.radio)
        pygame.draw.rect(pantalla, (255, 255, 255), self.rect, width=2, border_radius=self.radio)

        textura = self.fuente.render(self.texto, True, self.color_texto)
        posicion = textura.get_rect(center=self.rect.center)
        pantalla.blit(textura, posicion)
