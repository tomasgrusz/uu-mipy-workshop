import pygame


ROWS = 10
COLUMNS = 10


def load_d10_faces(sheet_path="sprites/d10-rainbow.png"):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    sheet_width, sheet_height = sheet.get_size()
    cell_width = sheet_width // COLUMNS
    cell_height = sheet_height // ROWS

    faces = []
    for row in range(ROWS):
        row_faces = []
        for column in range(COLUMNS):
            frame = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            frame.blit(
                sheet,
                (0, 0),
                pygame.Rect(column * cell_width, row * cell_height, cell_width, cell_height),
            )
            row_faces.append(frame)
        faces.append(row_faces)

    return faces


def get_face(faces, value, color_variant=0):
    return faces[color_variant][value]


def scale_face(face, size):
    return pygame.transform.scale(face, (size, size))