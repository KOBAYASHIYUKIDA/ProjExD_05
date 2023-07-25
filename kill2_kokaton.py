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
    引数 obj：オブジェクト（爆弾，猫，ビーム）SurfaceのRect
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
    引数2 dst：猫SurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（猫）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
    }

    def __init__(self, xy: tuple[int, int]):
        """
        猫画像Surfaceを生成する
        引数1 xy：猫画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/cat.png"), 0, 0.1)
        self.image = pg.transform.flip(img0, True, False)  # デフォルトの猫
        self.dire = (+1, 0)
        self.rect = self.image.get_rect()
        self.rect.left = 0
        self.speed = 10


    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じて猫を移動させる
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
        引数 bird：ビームを放つ猫
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), 0, 2.0)
        self.rect = self.image.get_rect()
        self.rect.left = bird.rect.right
        self.rect.centery = bird.rect.centery
        self.vx, self.vy = +5, 0
        self.speed = 5
    def speedup(self,speed):
        self.speed = speed

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, 0)
        if check_bound(self.rect) != (True, True):
            self.kill()
        

class Item(pg.sprite.Sprite):   
    """"
    アイテムによって、攻撃スピードアップ

    """
    def __init__(self):
     
     super().__init__()
     self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/22961558.png"), 0, 0.05)
     self.rect = self.image.get_rect()
     self.rect.left = WIDTH #
     self.rect.centery = random.randint(0,600)
     self.vx, self.vy = -5, 0
     self.speed = 3 #アイテムのスピード

     
    def update(self, screen: pg.Surface):
     
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        screen.blit(self.image, self.rect)
        #if check_bound(self.rect) != (True, True):
           #self.life_guage +=10


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
    敵に関するクラス
    """

    imgs = [pg.transform.rotozoom(pg.image.load(f"ex05/fig/monster1.png"), 0, 0.5),
            pg.transform.rotozoom(pg.image.load(f"ex05/fig/monster2.png"), 0, 0.5),
            pg.transform.rotozoom(pg.image.load(f"ex05/fig/monster3.png"), 0, 0.5)]
    def __init__(self):
        super().__init__()
        self.num = random.randint(0, 2)
        self.image = self.imgs[self.num]
        self.rect = self.image.get_rect()
        self.rect.right = WIDTH
        self.vy = +6
        self.bound = random.randint(30, HEIGHT)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.score = self.num+1
        self.interval = random.randint(50, 300)  # Beam射撃インターバル

    def update(self):
        """
        敵を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy     


class EnemyBeam(pg.sprite.Sprite):
    """
    Enemyの攻撃に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象の猫
        """
        super().__init__()
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*10, 2*10))
        pg.draw.circle(self.image, color, (10, 10), 10)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery
        self.vy = 0
        if emy.num == 0:
            self.speed = 3
        elif emy.num == 1:
            self.speed = 6
            self.vy = random.randint(-1, 1)
        else:
            self.speed = 10

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(-self.speed, self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()



class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """

    def __init__(self, emy: Enemy):
        super().__init__()
        #im = random.randint(0, len(__class__.imgs))
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
        self.rect.center = WIDTH-100, HEIGHT-50

    def boss_lifes(self, dm):
        self.life += dm

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"LIFE: {self.life}", 0, self.color)
        screen.blit(self.image, self.rect)


class Life_gauge: #体力ゲージに関するクラス
    def __init__(self):  
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.life_guage = 100 #体力は100から消費する
        self.image = self.font.render(f"Power: {self.life_guage}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 300, HEIGHT-50
       

    def life_gauge_down(self, d): 
        self.life_guage -= d #体力を引いていく
        
    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Power: {self.life_guage}", 0, self.color)
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("倒せ！猫！")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    life_gauge = Life_gauge()
    boss_life = Boss_life()
    boses = Last_boss()
    bird = Bird( (900, 400))
    beam= Beam(bird)
    enemyBeams = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    score = Score(emys)
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

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                enemyBeams.add(EnemyBeam(emy, bird))

        if tmr%500 == 0 :  # 500フレームに1回，アイテムを出現させる
            item = Item()

        
        #for item in pg.sprite.groupcollide(item, bird, True, True).keys():

        if item is not None:
    
            if item.rect.colliderect(bird.rect):
               item = None #アイテムに触れたらアイテムの表示を消す

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            if emy.num == 0:
                score.score_up(5) # 5点アップ
            elif emy.num == 1:
                score.score_up(10) # 10点アップ
            elif emy.num == 2:
                score.score_up(15) # 15点アップ

        if score.score >= 100 and num == 0:
            boss_life.update(screen)
            bg_img = pg.transform.rotozoom(pg.image.load(f"ex05/fig/pg_bg2.jpg"), 0, 2.0)
            boss.add(Last_boss())
            num = 1
        else:
            if tmr%200 == 0 and num == 0:
                emys.add(Enemy())# 200フレームに1回，敵機を出現させる
        

        if boss_life.life >= 1:
            for b in pg.sprite.groupcollide(boss, beams, False, True).keys():
                boss_life.boss_lifes(-1)
                exps.add(Explosion(b, 100))
                if boss_life.life == 0:
                    score.score_up(100)
                    pg.display.update()

        for enemyBeam in pg.sprite.groupcollide(enemyBeams, beams, True, True).keys():
            exps.add(Explosion(enemyBeam, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        if len(pg.sprite.spritecollide(bird, enemyBeams, True)) != 0:
            life_gauge.life_gauge_down(50)
        screen.blit(bg_img, [0, 0])

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        enemyBeams.update()
        enemyBeams.draw(screen)
        exps.update()
        exps.draw(screen)
        boss.update()
        boss.draw(screen)
        score.update(screen)
        life_gauge.update(screen)

        if item is not None:
            item.update(screen)
            #item.draw(screen)
        elif item is None:
            beams.update()
            beams.update()#ビームを加速させる
            beams.draw(screen)
        boss_life.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

        if life_gauge.life_guage == 0:
            time.sleep(2)
            return
        
        if boss_life.life == 0:
            time.sleep(3)
            return


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()