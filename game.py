import pygame
import random
import math
import sys

# Инициализация Pygame
pygame.init()

# Константы экрана
WIDTH, HEIGHT = 800, 600
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_PURPLE = (50, 0, 80)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Параметры гравитации черной дыры
GRAVITY_STRENGTH = 150
BLACK_HOLE_MASS = 500

# ----------------------------------------------------------------------
# Базовый класс Asteroid
# ----------------------------------------------------------------------
class Asteroid:
    def __init__(self, x, y, vx, vy, radius, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.alive = True

    def update(self, dt, all_objects=None, screen_width=WIDTH, screen_height=HEIGHT):
        """Обновление позиции по скорости и телепортация через границы."""
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Телепортация
        if self.x < 0:
            self.x = screen_width
        elif self.x > screen_width:
            self.x = 0
        if self.y < 0:
            self.y = screen_height
        elif self.y > screen_height:
            self.y = 0

    def draw(self, surface):
        """Отрисовка круга."""
        if self.alive:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def handle_collision(self, other, objects_list=None):
        """
        Реакция на столкновение с другим объектом.
        Для астероида: упругий отскок от другого астероида.
        """
        if not self.alive or not other.alive:
            return
        if isinstance(other, Asteroid) and not isinstance(other, (Comet, BlackHole)):
            self.resolve_elastic_collision(other)

    def resolve_elastic_collision(self, other):
        """Упругое столкновение двух кругов (изменение скоростей)."""
        # Вектор от self к other
        dx = other.x - self.x
        dy = other.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        nx = dx / dist
        ny = dy / dist

        # Относительная скорость вдоль нормали
        vrelx = other.vx - self.vx
        vrely = other.vy - self.vy
        vrel_n = vrelx * nx + vrely * ny

        if vrel_n > 0:
            return

        # Массы (считаем одинаковыми)
        m1 = self.radius ** 2
        m2 = other.radius ** 2
        e = 1.0  # коэффициент упругости

        # Импульс
        imp = (1 + e) * vrel_n / ( (1/m1) + (1/m2) )

        self.vx += imp * nx / m1
        self.vy += imp * ny / m1
        other.vx -= imp * nx / m2
        other.vy -= imp * ny / m2

    def is_alive(self):
        return self.alive


# ----------------------------------------------------------------------
# Комета (наследник Asteroid)
# ----------------------------------------------------------------------
class Comet(Asteroid):
    def __init__(self, x, y, vx, vy, radius):
        super().__init__(x, y, vx, vy, radius, YELLOW)
        self.tail_length = 10  # длина хвоста (в пикселях)

    def update(self, dt, all_objects=None, screen_width=WIDTH, screen_height=HEIGHT):
        """Комета движется с небольшим случайным ускорением (плавный поворот)."""
        if not self.alive:
            return
        # Случайное изменение направления (плавный поворот)
        self.vx += random.uniform(-5, 5) * dt
        self.vy += random.uniform(-5, 5) * dt
        # Ограничение скорости
        max_speed = 200
        speed = math.hypot(self.vx, self.vy)
        if speed > max_speed:
            self.vx = self.vx / speed * max_speed
            self.vy = self.vy / speed * max_speed
        super().update(dt, all_objects, screen_width, screen_height)

    def draw(self, surface):
        """Рисуем комету: желтый круг и хвост (линия против движения)."""
        if not self.alive:
            return
        # Хвост: линия от центра в направлении, противоположном скорости
        speed = math.hypot(self.vx, self.vy)
        if speed > 0.1:
            # Нормализованное направление хвоста (противоположное движению)
            tx = -self.vx / speed
            ty = -self.vy / speed
            tail_end_x = self.x + tx * self.tail_length
            tail_end_y = self.y + ty * self.tail_length
            pygame.draw.line(surface, ORANGE, (self.x, self.y), (tail_end_x, tail_end_y), 3)
        # Рисуем саму комету
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def handle_collision(self, other, objects_list=None):
        """При столкновении с кем-либо (кроме черной дыры) комета взрывается."""
        if not self.alive:
            return
        # Если столкнулись с черной дырой — не взрываемся (будем поглощены)
        if isinstance(other, BlackHole):
            return
        # Взрыв: комета исчезает и порождает осколки
        self.alive = False
        if objects_list is not None:
            self.explode(objects_list)

    def explode(self, objects_list):
        """Создаёт мелкие осколки (фрагменты) в месте кометы."""
        num_fragments = random.randint(5, 10)
        for _ in range(num_fragments):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.randint(2, 5)
            fragment = Fragment(self.x, self.y, vx, vy, radius, ORANGE, lifetime=2.0)
            objects_list.append(fragment)


# ----------------------------------------------------------------------
# Фрагмент (осколок) – маленький астероид с ограниченным временем жизни
# ----------------------------------------------------------------------
class Fragment(Asteroid):
    def __init__(self, x, y, vx, vy, radius, color, lifetime=2.0):
        super().__init__(x, y, vx, vy, radius, color)
        self.born_time = pygame.time.get_ticks() / 1000.0
        self.lifetime = lifetime

    def update(self, dt, all_objects=None, screen_width=WIDTH, screen_height=HEIGHT):
        """Обновление позиции и проверка таймера жизни."""
        if not self.alive:
            return
        super().update(dt, all_objects, screen_width, screen_height)
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.born_time > self.lifetime:
            self.alive = False


# ----------------------------------------------------------------------
# Чёрная дыра (наследник Asteroid)
# ----------------------------------------------------------------------
class BlackHole(Asteroid):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 0, 0, radius, DARK_PURPLE)
        self.spawn_time = pygame.time.get_ticks() / 1000.0
        self.lifetime = random.uniform(15, 20)  # через 15-20 секунд исчезает

    def update(self, dt, all_objects=None, screen_width=WIDTH, screen_height=HEIGHT):
        """Чёрная дыра не движется, но притягивает другие объекты."""
        if not self.alive:
            return
        # Проверка времени жизни
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.spawn_time > self.lifetime:
            self.alive = False
            return

        # Притяжение всех объектов (кроме себя)
        if all_objects is not None:
            for obj in all_objects:
                if obj is self or not obj.alive:
                    continue
                if isinstance(obj, BlackHole):
                    continue
                # Вектор от obj к чёрной дыре
                dx = self.x - obj.x
                dy = self.y - obj.y
                dist2 = dx*dx + dy*dy
                if dist2 < 1:
                    dist2 = 1
                dist = math.sqrt(dist2)
                # Сила притяжения (ускорение)
                force = GRAVITY_STRENGTH * BLACK_HOLE_MASS / (dist2 + 100)
                ax = force * dx / dist
                ay = force * dy / dist
                obj.vx += ax * dt
                obj.vy += ay * dt
                # Не даём объектам развить слишком большую скорость
                max_speed = 500
                speed = math.hypot(obj.vx, obj.vy)
                if speed > max_speed:
                    obj.vx = obj.vx / speed * max_speed
                    obj.vy = obj.vy / speed * max_speed

    def draw(self, surface):
        """Рисуем чёрную дыру с красноватым/фиолетовым ореолом."""
        if not self.alive:
            return
        # Внешний ореол
        for i in range(3):  # Рисуем несколько колец
            ring_radius = self.radius + i * 3 + 2
            if ring_radius > self.radius + 12:
                break
            # Плавное изменение цвета
            alpha = max(50, 150 - i * 30)
            color = (min(255, DARK_PURPLE[0] + alpha // 2),
                     max(0, DARK_PURPLE[1] - alpha // 4),
                     min(255, DARK_PURPLE[2] + alpha))
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), ring_radius, 2)
        # Сама дыра
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Внутреннее свечение
        pygame.draw.circle(surface, (80, 0, 100), (int(self.x), int(self.y)), self.radius - 3)

    def handle_collision(self, other, objects_list=None):
        """При столкновении чёрная дыра поглощает любой другой объект."""
        if not self.alive or not other.alive:
            return
        if isinstance(other, BlackHole):
            return
        other.alive = False


# ----------------------------------------------------------------------
# Функции для генерации объектов
# ----------------------------------------------------------------------
def objects_overlap(new_obj, existing_objects, margin=20):
    """Проверяет, пересекается ли новый объект с уже существующими."""
    for obj in existing_objects:
        if math.hypot(new_obj.x - obj.x, new_obj.y - obj.y) < (new_obj.radius + obj.radius + margin):
            return True
    return False

def generate_random_position(existing_objects, radius, margin=30):
    """Генерирует случайную позицию, не пересекающуюся с existing_objects."""
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.uniform(radius, WIDTH - radius)
        y = random.uniform(radius, HEIGHT - radius)
        temp_obj = Asteroid(x, y, 0, 0, radius, WHITE)  # фиктивный объект для проверки
        if not objects_overlap(temp_obj, existing_objects, margin):
            return x, y
    # Если не нашли – возвращаем позицию с отступом
    return random.uniform(radius*2, WIDTH - radius*2), random.uniform(radius*2, HEIGHT - radius*2)

def create_initial_objects():
    """Создаёт начальный набор: 3 астероида, 2 кометы, 1 чёрная дыра."""
    objects = []
    # Сначала создаём чёрную дыру (можно в центре)
    bh_radius = 20
    bh = BlackHole(WIDTH // 2, HEIGHT // 2, bh_radius)
    objects.append(bh)

    # Астероиды
    for _ in range(3):
        radius = random.randint(10, 20)
        x, y = generate_random_position(objects, radius)
        vx = random.uniform(-80, 80)
        vy = random.uniform(-80, 80)
        color = BROWN if random.random() > 0.5 else GRAY
        asteroid = Asteroid(x, y, vx, vy, radius, color)
        objects.append(asteroid)

    # Кометы
    for _ in range(2):
        radius = random.randint(8, 15)
        x, y = generate_random_position(objects, radius)
        vx = random.uniform(-70, 70)
        vy = random.uniform(-70, 70)
        comet = Comet(x, y, vx, vy, radius)
        objects.append(comet)

    return objects

def regenerate(objects):
    """Очищает список и создаёт новый набор объектов."""
    objects.clear()
    objects.extend(create_initial_objects())

# ----------------------------------------------------------------------
# GUI: кнопка Restart и пауза
# ----------------------------------------------------------------------
def draw_button(surface, text, x, y, w, h, color, hover_color, action=None):
    """Рисует кнопку и возвращает True, если по ней кликнули."""
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse):
        pygame.draw.rect(surface, hover_color, rect)
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(surface, color, rect)
    font = pygame.font.Font(None, 30)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)
    return rect

# ----------------------------------------------------------------------
# Основная функция
# ----------------------------------------------------------------------
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Asteroid Simulation")
    clock = pygame.time.Clock()

    objects = create_initial_objects()
    paused = False
    regeneration_timer = None
    regeneration_delay = 2.0  # секунд

    # Шрифт для счётчиков
    font = pygame.font.Font(None, 36)
    restart_rect = pygame.Rect(WIDTH-110, 10, 100, 40)  # Определяем здесь

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # время в секундах
        current_time = pygame.time.get_ticks() / 1000.0

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Проверка клика по кнопке Restart
                if restart_rect.collidepoint(event.pos):
                    regenerate(objects)
                    regeneration_timer = None
                    paused = False

        # Обновление (если не на паузе)
        if not paused:
            # Сначала обновляем позиции и гравитацию (black holes влияют на других)
            for obj in objects:
                if isinstance(obj, BlackHole):
                    obj.update(dt, objects, WIDTH, HEIGHT)
                else:
                    obj.update(dt, None, WIDTH, HEIGHT)

            # Обработка столкновений (проверяем все пары)
            objects_copy = objects[:]
            n = len(objects_copy)
            for i in range(n):
                obj1 = objects_copy[i]
                if not obj1.alive:
                    continue
                for j in range(i+1, n):
                    obj2 = objects_copy[j]
                    if not obj2.alive:
                        continue
                    # Проверка столкновения
                    dx = obj1.x - obj2.x
                    dy = obj1.y - obj2.y
                    dist = math.hypot(dx, dy)
                    if dist < obj1.radius + obj2.radius:
                        # Вызываем реакции
                        obj1.handle_collision(obj2, objects)
                        obj2.handle_collision(obj1, objects)

            # Удаление мёртвых объектов
            objects[:] = [obj for obj in objects if obj.is_alive()]

            # Проверка, остались ли только фрагменты или вообще ничего
            main_objects = [obj for obj in objects if not isinstance(obj, Fragment)]
            if len(main_objects) == 0:
                if regeneration_timer is None:
                    regeneration_timer = current_time
                elif current_time - regeneration_timer >= regeneration_delay:
                    regenerate(objects)
                    regeneration_timer = None
            else:
                regeneration_timer = None

        # Отрисовка
        screen.fill(BLACK)

        for obj in objects:
            obj.draw(screen)

        # Счётчики объектов
        asteroid_count = sum(1 for obj in objects if isinstance(obj, Asteroid) and not isinstance(obj, (Comet, BlackHole, Fragment)))
        comet_count = sum(1 for obj in objects if isinstance(obj, Comet))
        blackhole_count = sum(1 for obj in objects if isinstance(obj, BlackHole))
        fragment_count = sum(1 for obj in objects if isinstance(obj, Fragment))

        text_asteroids = font.render(f"Asteroids: {asteroid_count}", True, WHITE)
        text_comets = font.render(f"Comets: {comet_count}", True, WHITE)
        text_bh = font.render(f"Black Holes: {blackhole_count}", True, WHITE)
        text_frag = font.render(f"Fragments: {fragment_count}", True, GRAY)
        screen.blit(text_asteroids, (10, 10))
        screen.blit(text_comets, (10, 50))
        screen.blit(text_bh, (10, 90))
        screen.blit(text_frag, (10, 130))

        if paused:
            pause_text = font.render("PAUSED - Press SPACE", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - 100, HEIGHT//2))

        # Кнопка Restart
        restart_rect = draw_button(screen, "RESTART", WIDTH-110, 10, 100, 40, BLUE, GREEN, lambda: (regenerate(objects), None))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()