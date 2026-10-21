import bpy
import os

# удаляем ВСЕ старые объекты, даже скрытые
for _o in list(bpy.data.objects):
    bpy.data.objects.remove(_o, do_unlink=True)
for _m in list(bpy.data.meshes):
    bpy.data.meshes.remove(_m)

# ---------- материалы ----------
def mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    # ищем по типу, а не по имени (в русском Blender имя узла другое)
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = color  # цвет для режима Solid
    return m

YELLOW = mat("Yellow", (1.0, 0.78, 0.05, 1))
BLUE   = mat("Blue",   (0.05, 0.22, 0.65, 1))
DARK   = mat("DarkBlue", (0.03, 0.14, 0.45, 1))
GRAY   = mat("Gray",   (0.62, 0.64, 0.68, 1), 0.4)
WHITE  = mat("White",  (1, 1, 1, 1), 0.3)
IRIS   = mat("Iris",   (0.35, 0.17, 0.05, 1), 0.3)
BLACK  = mat("Black",  (0.02, 0.02, 0.02, 1))

parts = []
part_x = {}   # x-позиция каждой детали: по ней определяем левую и правую сторону
SCALE = 1.1   # общий размер миньона (+10%)

def box(name, loc, size, material):
    """size = полные размеры (x, y, z)"""
    loc = tuple(c * SCALE for c in loc)
    size = tuple(c * SCALE for c in size)
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    # применяем ТОЛЬКО масштаб (по умолчанию Blender применяет и позицию тоже)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    part_x[o] = loc[0]          # запоминаем сторону (лево/право) заранее
    parts.append(o)
    return o

def box_z(name, x, y, z0, z1, w, d, material):
    """Коробка по высоте от z0 до z1 (удобно складывать стопкой)"""
    return box(name, (x, y, (z0 + z1) / 2), (w, d, z1 - z0), material)

# ВАЖНО: детали разных цветов только соприкасаются, но не накладываются
# друг на друга одинаковыми плоскостями -> нет мерцающих полос (z-fighting).
# Перёд = -Y.

# ---------- размеры (все высоты в одном месте) ----------
W, D = 1.0, 0.85                  # ширина и глубина тела
HALF_W, HALF_D = W / 2, D / 2

LEG_TOP   = 0.36                  # верх ног = низ комбинезона
BODY_TOP  = 0.88                  # верх комбинезона = низ головы
PLATE_H   = 0.12                  # высота верхней пластины головы
HEAD_TOP  = 1.68                  # самая верхняя точка головы (чуть выше прежнего)
INSET     = 0.09                  # на сколько верхняя пластина меньше
BAND_Z0, BAND_Z1 = 1.10, 1.28     # ремешок очков
EYE_Z     = (BAND_Z0 + BAND_Z1) / 2   # центр глаза = центр ремешка
LW, LD, LEG_X = 0.36, 0.45, 0.28  # нога: ширина, глубина, расстояние от центра
LEG_INSET = 0.12                 # на сколько нога заходит внутрь тела (чтобы не было щели при движении)
AW, AD    = 0.14, 0.22            # рука: ширина, глубина
ARM_TOP, ARM_BOT, HAND_BOT = 1.04, 0.56, 0.44   # руки как раньше

# ---------- ботинки и ноги ----------
for s, side in ((-1, "R"), (1, "L")):
    box_z(f"Shoe_{side}", s * LEG_X, -0.08, 0.00, 0.12, LW + 0.02, 0.62, BLACK)
    box_z(f"Leg_{side}",  s * LEG_X,  0.00, 0.12, LEG_TOP + LEG_INSET, LW, LD, BLUE)  # верх ноги спрятан внутри тела

# ---------- синий комбинезон ----------
box_z("Overalls", 0, 0, LEG_TOP, BODY_TOP, W, D, BLUE)
# передний карман: тёмный, сверху светлый кант
box_z("Pocket",    0, -HALF_D - 0.01, 0.52, 0.74, 0.34, 0.02, DARK)
box_z("PocketTop", 0, -HALF_D - 0.03, 0.70, 0.74, 0.34, 0.02, BLUE)
# лямки (заканчиваются под ремешком, чтобы не накладываться на него)
STRAP_TOP = BAND_Z0 - 0.02
for s in (-1, 1):
    box_z(f"Strap_{s}", s * 0.30, -HALF_D - 0.01, BODY_TOP, STRAP_TOP, 0.14, 0.02, BLUE)

# ---------- голова: большой блок + сверху меньшая пластина (ступенька) ----------
box_z("Head", 0, 0, BODY_TOP, HEAD_TOP - PLATE_H, W, D, YELLOW)
box_z("Head_Top", 0, 0, HEAD_TOP - PLATE_H, HEAD_TOP, W - INSET * 2, D - INSET * 2, YELLOW)

# ---------- чёрный ремешок очков ----------
box_z("Goggle_Band", 0, 0, BAND_Z0, BAND_Z1, W + 0.04, D + 0.04, BLACK)

# ---------- очки и глаз (как на референсе) ----------
FRONT = -HALF_D
box("Goggle_Frame", (0, FRONT - 0.05, EYE_Z), (0.42, 0.10, 0.42), GRAY)          # серая оправа
box("Eye_White",    (0, FRONT - 0.105, EYE_Z), (0.32, 0.04, 0.32), WHITE)        # белок
EX, EZ = 0.03, 0.02                                                              # лёгкий сдвиг взгляда
box("Eye_Iris",     (EX, FRONT - 0.130, EYE_Z + EZ), (0.18, 0.03, 0.18), IRIS)    # радужка
box("Eye_Pupil",    (EX, FRONT - 0.152, EYE_Z + EZ), (0.09, 0.014, 0.09), BLACK)  # зрачок
box("Eye_Shine",    (EX + 0.045, FRONT - 0.149, EYE_Z + EZ + 0.045), (0.03, 0.008, 0.03), WHITE)  # блик

# ---------- волосики: ряд поперёк головы на верхней пластине ----------
hair = ((-0.22, 0.04), (0.0, 0.09), (0.22, 0.04))   # (смещение по X, высота)
for i, (x, h) in enumerate(hair):
    box_z(f"Hair_{i}", x, 0, HEAD_TOP, HEAD_TOP + h, 0.12, 0.12, BLACK)

# ---------- руки: прижаты к телу, длинные и нетолстые ----------
for s_, side in ((-1, "R"), (1, "L")):
    ax = s_ * (HALF_W + AW / 2)
    box_z(f"Arm_{side}",  ax, 0, ARM_BOT, ARM_TOP, AW, AD, YELLOW)
    box_z(f"Hand_{side}", ax, 0, HAND_BOT, ARM_BOT, AW, AD, BLACK)

# ---------- детали сзади ----------
BACK = HALF_D
for s_ in (-1, 1):
    box_z(f"BackStrap_{s_}", s_ * 0.30, BACK + 0.01, BODY_TOP, STRAP_TOP, 0.14, 0.02, BLUE)
    box_z(f"BackPocket_{s_}", s_ * 0.22, BACK + 0.01, 0.46, 0.70, 0.30, 0.02, DARK)
    box_z(f"PocketTop_{s_}",  s_ * 0.22, BACK + 0.03, 0.66, 0.70, 0.30, 0.02, BLUE)
box_z("BackSeam", 0, BACK + 0.01, LEG_TOP, LEG_TOP + 0.10, 0.04, 0.02, DARK)

# ---------- разделить на части для Roblox ----------
# Центр вращения (origin) стоит в суставе: руки - в плече, ноги - в бедре.
def group_of(o):
    # персонаж смотрит в -Y, его правая сторона = -X
    right = part_x[o] < 0
    if o.name.startswith(("Arm_", "Hand_")):
        return "RightArm" if right else "LeftArm"
    if o.name.startswith(("Shoe_", "Leg_")):
        return "RightLeg" if right else "LeftLeg"
    return "Torso"

groups = {}
for o in parts:
    groups.setdefault(group_of(o), []).append(o)

pivots = {
    "Torso":    (0, 0, LEG_TOP),
    "RightArm": (-(HALF_W + AW / 2), 0, ARM_TOP),
    "LeftArm":  ( (HALF_W + AW / 2), 0, ARM_TOP),
    "RightLeg": (-LEG_X, 0, LEG_TOP),
    "LeftLeg":  ( LEG_X, 0, LEG_TOP),
}

result = {}
for gname, objs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = gname
    bpy.ops.object.shade_flat()
    bpy.context.scene.cursor.location = tuple(c * SCALE for c in pivots[gname])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    result[gname] = obj
bpy.context.scene.cursor.location = (0, 0, 0)

# ---------- экспорт для Roblox Studio (FBX) ----------
EXPORT = True
if EXPORT:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for o in result.values():
            o.select_set(True)
        bpy.ops.export_scene.fbx(filepath=os.path.join(desktop, "minion_parts.fbx"),
                                 use_selection=True, object_types={'MESH'},
                                 path_mode='COPY', embed_textures=True)
        # каждая часть ещё и отдельным файлом
        folder = os.path.join(desktop, "minion_parts")
        os.makedirs(folder, exist_ok=True)
        for name, o in result.items():
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.ops.export_scene.fbx(filepath=os.path.join(folder, name + ".fbx"),
                                     use_selection=True, object_types={'MESH'},
                                     path_mode='COPY', embed_textures=True)
        print("FBX сохранены в:", desktop)
    except Exception as e:
        print("Экспорт не удался, сделай File > Export > FBX вручную:", e)

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces[0].shading.type = 'MATERIAL'

print("Готово. Объекты:", [o.name for o in bpy.data.objects])
