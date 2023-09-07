import chess
import chess.pgn
import chess.engine
import chess.svg
from enum import Enum
import cairosvg
import os
from PIL import Image
from PIL import ImageDraw

def main():
    game = chess.pgn.read_game(open("game.pgn"))
    engine = chess.engine.SimpleEngine.popen_uci("stockfish_x86-64-avx2.exe")
    engine.configure({"Threads": 4})

    images = []
    default_board = chess.Board()
    info = engine.analyse(default_board, chess.engine.Limit(time = 1.))
    engine_moves = info["pv"]
    engine_move_san = default_board.san(info["pv"][0])
    last_eval = info["score"]
    player = chess.WHITE
    move = 1

    class MoveRate(Enum):
        BestMove = 0
        Excellent = 1
        Good = 2
        Inaccuracy = 3
        Mistake = 4
        Blunder = 5
        Miss = 6
        Brilliant = 7
        GreatMove = 8

    def determine_color(rating: MoveRate) -> str:
        if rating is not None:
            match rating:
                case MoveRate.BestMove:
                    return "#2DFF38"
                case MoveRate.Excellent:
                    return "#1B9621"
                case MoveRate.Good:
                    return "#66CE61"
                case MoveRate.Inaccuracy:
                    return "#FFE400"
                case MoveRate.Mistake:
                    return "#FF9700"
                case MoveRate.Blunder:
                    return "#BA0000"
                case MoveRate.Miss:
                    return "#FF4949"
                case MoveRate.Brilliant:
                    return "#00BAC9"
                case MoveRate.GreatMove:
                    return "#0094FF"
        else:
            return "#404040"

    for node in game.mainline():
        print("Evaluating Move " + str(move))
        move += 1

        board = node.board()
        info = engine.analyse(board, chess.engine.Limit(time = 1.))

        _eval = info["score"].pov(player)
        last_eval = last_eval.pov(player)
        
        rating = None

        if not _eval.is_mate():
            if not last_eval.is_mate():
                if node.uci() == engine_moves[0].uci() or _eval.score() >= last_eval.score():
                    rating = MoveRate.BestMove
                elif abs(_eval.score() - last_eval.score()) < 15:
                    rating = MoveRate.Excellent
                elif abs(_eval.score() - last_eval.score()) < 50:
                    rating = MoveRate.Good
                elif abs(_eval.score() - last_eval.score()) < 250:
                    rating = MoveRate.Inaccuracy
                elif abs(_eval.score() - last_eval.score()) < 600:
                    rating = MoveRate.Mistake
                else:
                    rating = MoveRate.Blunder
            else:
                if _eval.score() >= 700:
                    rating = MoveRate.Miss
                elif _eval.score() >= 500:
                    rating = MoveRate.Good
                elif _eval.score() >= 200:
                    rating = MoveRate.Inaccuracy
                else:
                    rating = MoveRate.Blunder
        else:
            if last_eval.is_mate():
                if node.uci() == engine_moves[0].uci() or _eval.mate() - last_eval.mate() >= 1 or _eval.mate() == 0:
                    rating = MoveRate.BestMove
                elif _eval.mate() - last_eval.mate() >= 0:
                    rating = MoveRate.Excellent
                else:
                    rating = MoveRate.Blunder
            else:
                if _eval.mate() > 0:
                    rating = MoveRate.GreatMove
                elif node.uci() != engine_moves[0].uci():
                    rating = MoveRate.Blunder
                else:
                    rating = MoveRate.BestMove

        arrows = []
        if node.uci() != engine_moves[0].uci() and (engine_moves[0].from_square != node.move.from_square or engine_moves[0].to_square != node.move.to_square):
            arrows = [chess.svg.Arrow(engine_moves[0].from_square, engine_moves[0].to_square, color = determine_color(MoveRate.BestMove))]
        arrows.append(chess.svg.Arrow(node.move.from_square, node.move.to_square, color = determine_color(rating)))

        svg_string = chess.svg.board(board, borders = True, arrows = arrows, lastmove = node.move)

        f = open("__temp.png", "wb")
        f.write(cairosvg.svg2png(svg_string))
        f.close()

        iboard = Image.open("__temp.png")
        image = Image.new("RGBA", (iboard.width, iboard.height + 21))
        image.paste(iboard, (0, 41))
        iboard.close()
        os.remove("__temp.png")
        draw = ImageDraw.Draw(image)
        _eval = info["score"].white()
        draw.rectangle((0, 0, image.width, 40), fill = "#000000")
        if _eval.is_mate():
            if _eval.mate() > 0:
                draw.rectangle((0, 0, image.width, 20), fill = "#FFFFFF")
            if _eval.mate() == 0:
                draw.text((5, 5), "Game Over", fill = "#FFFFFF", anchor = "lm")
            elif _eval.mate() > 0:
                draw.text((5, 5), "M" + str(_eval.mate()), fill = "#000000", anchor = "lm")
            else:
                offset = len("M" + str(-_eval.mate())) * 6
                draw.text((image.width - (4 + offset), 5), "M" + str(-_eval.mate()), fill = "#FFFFFF", anchor = "rm", align = "right")
        else:
            draw.rectangle((0, 0, (image.width / 2) + max(min(_eval.score() / 10, (image.width / 2) - 10), (-image.width / 2) + 10) , 20), fill = "#FFFFFF")
            if _eval.score() >= 0:
                draw.text((5, 5), str(round(_eval.score() / 100, 2)), fill = "#000000", anchor = "lm")
            else:
                offset = len(str(-round(_eval.score() / 100, 2))) * 6
                draw.text((image.width - (4 + offset), 5), str(-round(_eval.score() / 100, 2)), fill = "#FFFFFF", anchor = "rm", align = "right")

        text = node.san()

        match rating:
            case MoveRate.BestMove:
                text += " is the Best Move"
            case MoveRate.Excellent:
                text += " is an Excellent Move"
            case MoveRate.Good:
                text += " is a Good Move"
            case MoveRate.Inaccuracy:
                text += " is an Inaccuracy"
            case MoveRate.Mistake:
                text += " is a Mistake"
            case MoveRate.Blunder:
                text += " is a Blunder"
            case MoveRate.Miss:
                text += " Missed an opportunity"
            case MoveRate.Brilliant:
                text += " is a Brilliant Move"
            case MoveRate.GreatMove:
                text += " is a Great Move"
        
        if node.uci() != engine_moves[0].uci():
            if rating == MoveRate.BestMove:
                text += ", an alternative is " + engine_move_san
            else:
                text += ", the Best Move was " + engine_move_san

        draw.text((5, 25), text, "#FFFFFF")

        images.append(image)

        if info["score"].is_mate():
            if info["score"].white().mate() == 0:
                break
        elif info["depth"] == 0:
            break

        engine_moves = info["pv"]
        engine_move_san = board.san(info["pv"][0])
        last_eval = info["score"]

        if player == chess.WHITE:
            player = chess.BLACK
        else:
            player = chess.WHITE

    print("Saving gif...")
    images[0].save("output.gif", save_all = True, append_images = images[1:], duration = 2500, loop = 0)
    print("Done!")

    engine.close()

if __name__ == "__main__":
    main()