import math
import random
import sys
import time


import pygame as pg


WIDTH = 1200  # ゲームウィンドウの幅
HEIGHT = 600  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/cat.png"), 0, 0.1)
        self.image = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.dire = (+1, 0)
        self.rect = self.image.get_rect()
        self.rect.left = 0
        self.speed = 10


    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]: 
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)

        screen.blit(self.image, self.rect)

  
    def get_direction(self) -> tuple[int, int]:
        return self.dire


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        引数に基づきビームSurfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), 0, 2.0)
        self.rect = self.image.get_rect()
        self.rect.left = bird.rect.right
        self.rect.centery = bird.rect.centery
        self.vx, self.vy = +5, 0
        self.speed = 5


    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill() 


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.right = WIDTH
        self.vy = +6
        self.bound = random.randint(0, HEIGHT)  # 停止位置
        self.state = "down"  # 降下状態or停止状態


    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add): #スコアを加算
        self.score += add


    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)

class Last_boss(pg.sprite.Sprite):
    """
    ラスボス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/7.png"), 0, 3.0)
        self.rect = self.image.get_rect()
        self.rect.right = WIDTH
        self.vy = +1

    def update(self):
        self.rect.centery += self.vy * 8
        # 画面端に到達したら方向を反転させる
        if self.rect.bottom >= HEIGHT or self.rect.top <= 0:
            self.vy *= -1

class Boss_life:
    """
    ボスの体力
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (255, 0, 0)
        self.life = 10
        self.image = self.font.render(f"LIFE: {self.life}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT

    def boss_lifes(self, dm):
        self.life += dm

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"LIFE: {self.life}", 0, self.color)
        screen.blit(self.image, self.rect)
        

def main():
    pg.display.set_caption("倒せ！こうかとん！")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    score = Score()
    boss_life = Boss_life()
    boses = Last_boss()
    bird = Bird( (900, 400))
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    boss = pg.sprite.Group()
    num = 0

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0

            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(50)  # 10点アップ
        
        if score.score >= 100 and num == 0:
            boss_life.update(screen)
            bg_img = pg.transform.rotozoom(pg.image.load(f"ex05/fig/pg_bg_2.jpg"), 0, 4.0)
            boss.add(Last_boss())
            num = 1
        else:
            if tmr%200 == 0 and num == 0:
                emys.add(Enemy())# 200フレームに1回，敵機を出現させる

        if boss_life.life != 1:
            for b in pg.sprite.groupcollide(boss, beams, False, True).keys():
                boss_life.boss_lifes(-1)
                exps.add(Explosion(b, 100))
        else:
            for bo in pg.sprite.groupcollide(boss, beams, True, True).keys():
                exps.add(Explosion(bo, 100))
                boss_life.boss_lifes(-1)
                score.score_up(100)
                pg.display.update()
                time.sleep(1)  # 100点アップ
                return

        screen.blit(bg_img, [0, 0])

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        exps.update()
        exps.draw(screen)
        boss.update()
        boss.draw(screen)
        score.update(screen)
        boss_life.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
