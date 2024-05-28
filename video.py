from PIL import Image
import json
import os
import io

log = print


# 转成灰度图
def grayimage(path):
    # convert('L') 转为灰度图
    # 这样每个像素点就只有一个灰度数据
    img = Image.open(path).convert('L')
    return img


# 求出[图块中 [每个像素的差的绝对值] 的和
def diff_image(img1, img2):
    # 求出[图块中 [每个像素的差的绝对值] 的和
    # 每个图块是 8x8 像素
    # 拿到图的宽高
    w, h = img1.size
    # 获取 pixels
    pixels1 = img1.load()
    pixels2 = img2.load()

    # 用于计算像素差的绝对值的和
    num = 0

    # 根据宽高循环，拿到 a, b 同一个像素点的值进行相减
    # 拿到差值的绝对值，进行相加
    for x in range(w):
        for y in range(h):
            p1 = pixels1[x, y]
            p2 = pixels2[x, y]
            # 累加 [图块中 [每个像素的差的绝对值]
            num += abs(p2 - p1)

    return num


# 图片裁剪
def image_crop(img, x, y, w, h):
    x2 = x + w
    y2 = y + h
    return img.crop((x, y, x2, y2))


def image_find(a, b, x, y):
    # 结束条件
    threshold = 50
    # 获取图片大小
    width, height = a.size

    # 在方圆为 4 的范围查找
    r = 4
    # 1，遍历 (x - r, y - r) 到 (x + r, y + r)
    for y2 in range(y - r, y + r):
        for x2 in range(x - r, x + r):
            # 超过图片大小，则跳过
            if x2 < 0 or x2 > width:
                continue
            if y2 < 0 or y2 > height:
                continue

            # 拿到 b 图块的大小
            w, h = b.size
            # 2. 从 a 图片中裁剪出 b 图块大小的 图块
            ba = image_crop(a, x2, y2, w, h)
            # 3. 拿到[图块中 [每个像素的差的绝对值] 的和
            s = diff_image(ba, b)
            # 4. 如果相似度小于终止条件，则返回 x, y 的位置
            # 如果相似度大于阈值，则返回 -2 作为标识，说明是当前作为新的关键帧
            if s < threshold:
                return x2, y2, ba

    # 循环结束还没找到，则返回 -1, -1, b 图块
    return -1, -1, b


def write_json(l):
    content = json.dumps(l, sort_keys=True, indent=2, separators=(',', ': '))
    fs = open('big_buck_bunny_08361.videoblock', 'w')
    fs.write(content)
    fs.close()


# 生成差值图
def putpixel_block(img, pixels1, b, x1, y1):
    pixels2 = b.load()
    # 8x8 的方块，用 b 减去这个方块的每一个像素
    # 得到差值，存到 img 中
    for y2 in range(8):
        for x2 in range(8):
            x = x1 + x2
            y = y1 + y2
            p1 = pixels1[x, y]
            p2 = pixels2[x2, y2]
            p = p1 - p2
            img.putpixel((x, y), p)


def encode(img1, img2):
    a = img1.convert('L')
    b = img2.convert('L')
    # 拿到宽高
    w, h = a.size
    # 8 像素
    size = 8
    pixels = b.load()
    l = []
    bs = Image.new('RGB', (w, h))
    # 图块数
    blocks = (w * h) / (8 * 8)
    log('blocks', blocks)
    # 当前图块超过 30%，则使用当前图作为新的关键帧
    threshold = 0.3

    # 把 b 切割成 8x8 像素的图块
    # 循环 0-h 步进为 8
    # 循环 0-w 步进为 8
    for y in range(0, h, size):
        for x in range(0, w, size):
            # 根据 x y 裁剪 8x8 像素的图块
            img = image_crop(b, x, y, size, size)
            x2, y2, ba = image_find(a, img, x, y)
            # 存入 json 数组
            l.append({
                'x': x2,
                'y': y2,
            })
            # x = -1 时，直接把图块覆盖到图片上
            # 否则，根据 json item x y 坐标裁剪图块
            # 在进行图块和相似图像素的差值
            # 差值 = p2[x, y] - 相似[x, y]
            # x = -2 时，说明差值太大
            # 直接返回当前的图作为新的关键帧，json 为空字符串
            if x2 == -1:
                ba = image_crop(img2, x, y, size, size)
                bs.paste(ba, (x, y))

            count = l.count({'x': -1, 'y': -1})
            if count > blocks * threshold:
                return '', b

    # # 把 json 数据写入文件中
    # write_json(l)
    # # 存差值图
    # bs.save('diff.jpg')
    json_str = json.dumps(l, sort_keys=True, indent=2, separators=(',', ': '))
    return json_str, bs


# 生成差值图
def restore_block(img, a, diffPixels, x1, y1):
    pixels = a.load()
    # 8x8 的方块，用 b 减去这个方块的每一个像素
    # 得到差值，存到 img 中
    for y2 in range(8):
        for x2 in range(8):
            x = x1 + x2
            y = y1 + y2
            p2 = diffPixels[x, y]
            p1 = pixels[x2, y2]
            p = p1 + p2
            img[x, y] = p


# 还原图片
def restore_image(a, b, data):
    # 8x8 像素
    size = 8
    # 拿到图片的宽高
    w, h = a.size

    # 根据宽高新建图块

    for y in range(0, h, size):
        for x in range(0, w, size):
            index = int(x / 8) + (int(y / 8) * int(w / 8))
            item = data[index]
            # x = -1 时，直接把图块覆盖到图片上
            # 否则，根据 json item x y 坐标裁剪图块
            # 在进行图块像素和 diff 图差值相加
            if item['x'] != -1:
                bs = image_crop(a, item['x'], item['y'], size, size)
                b.paste(bs, (x, y))

    return b


def main():
    # encode_of_uipn2()
    # imgs = decode_of_uipn2()
    # window(imgs)
    pass


if __name__ == '__main__':
    main()
