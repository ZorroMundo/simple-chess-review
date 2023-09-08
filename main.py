import chess
import chess.pgn
import chess.engine
import chess.svg
import math
import cairosvg
import os
import copy
from enum import Enum
from PIL import Image
from PIL import ImageDraw

def main():

    game = chess.pgn.read_game(open("game.pgn"))
    engine = chess.engine.SimpleEngine.popen_uci("stockfish_x86-64-avx2.exe")
    engine.configure({"Threads": 4})

    orientation = chess.WHITE
    images = []
    info = engine.analyse(game.board(), chess.engine.Limit(time = 1.))
    engine_moves = info["pv"]
    engine_move_san = game.board().san(info["pv"][0])
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
    def player_accuracy(_dict: dict[MoveRate, int]) -> float:
        current = 0
        full = 0

        current += _dict[MoveRate.BestMove] * 300
        full += _dict[MoveRate.BestMove] * 300

        current += _dict[MoveRate.Excellent] * 250
        full += _dict[MoveRate.Excellent] * 300

        current += _dict[MoveRate.Good] * 200
        full += _dict[MoveRate.Good] * 300

        current += _dict[MoveRate.Inaccuracy] * 150
        full += _dict[MoveRate.Inaccuracy] * 300

        current += _dict[MoveRate.Mistake] * 100
        full += _dict[MoveRate.Mistake] * 300

        current += _dict[MoveRate.Blunder] * 5
        full += _dict[MoveRate.Blunder] * 300

        current += _dict[MoveRate.Miss] * 100
        full += _dict[MoveRate.Miss] * 300

        current += _dict[MoveRate.Brilliant] * 300
        full += _dict[MoveRate.Brilliant] * 300

        current += _dict[MoveRate.GreatMove] * 300
        full += _dict[MoveRate.GreatMove] * 300
        
        return (current / full) * 100.

    white = {
       MoveRate.BestMove: 0,
       MoveRate.Excellent: 0,
       MoveRate.Good: 0,
       MoveRate.Inaccuracy: 0,
       MoveRate.Mistake: 0,
       MoveRate.Blunder: 0,
       MoveRate.Miss: 0,
       MoveRate.Brilliant: 0,
       MoveRate.GreatMove: 0 
    }
    black = copy.deepcopy(white)
    evaluations = []

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
                if node.uci() == engine_moves[0].uci():
                    rating = MoveRate.BestMove
                elif _eval.score() >= last_eval.score():
                    rating = MoveRate.GreatMove
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
                elif _eval.mate() - last_eval.mate() == 0 or _eval.mate() >= 0:
                    rating = MoveRate.Excellent
                else:
                    rating = MoveRate.Blunder
            else:
                if _eval.mate() > 0:
                    rating = MoveRate.GreatMove
                elif node.uci() == engine_moves[0].uci():
                    rating = MoveRate.BestMove
                else:
                    rating = MoveRate.Blunder

        arrows = []
        if node.uci() != engine_moves[0].uci() and (engine_moves[0].from_square != node.move.from_square or engine_moves[0].to_square != node.move.to_square):
            arrows = [chess.svg.Arrow(engine_moves[0].from_square, engine_moves[0].to_square, color = determine_color(MoveRate.BestMove))]
        arrows.append(chess.svg.Arrow(node.move.from_square, node.move.to_square, color = determine_color(rating)))

        board.turn = chess.WHITE if player == chess.BLACK else chess.BLACK
        check = None
        if board.is_check():
            check = board.king(board.turn)
        svg_string = chess.svg.board(board, borders = True, arrows = arrows, lastmove = node.move, check = check, orientation = orientation)

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
            score = 0.5
            if _eval.score() > 0:
                score = 0.5 + min(abs(_eval.score() / 1000), 0.48)
            elif _eval.score() < 0:
                score = 0.5 - min(abs(_eval.score() / 1000), 0.48)
            draw.rectangle((0, 0, image.width * score, 20), fill = "#FFFFFF")
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

        _dict = white

        if player == chess.WHITE:
            player = chess.BLACK
        else:
            _dict = black
            player = chess.WHITE
        
        _dict[rating] += 1
        evaluations.append(last_eval)

    engine.close()
    image = Image.new("RGBA", (images[0].width, images[0].height + 21))
    draw = ImageDraw.Draw(image)
    width = math.floor(image.width / 1.5)
    x_add = width / len(evaluations)
    index = 0
    draw.rectangle((0, 0, image.width, image.height), "#000000")

    while index < len(evaluations):
        score = 0.5
        _eval = evaluations[index].white()
        if _eval.is_mate():
            if _eval.mate() > 0:
                score = 1
            else:
                score = -1
        else:
            if _eval.score() > 0:
                score = 0.5 + min(abs(_eval.score() / 1000), 0.45)
            elif _eval.score() < 0:
                score = 0.5 - min(abs(_eval.score() / 1000), 0.45)
        if score > 0:
            draw.rectangle((65 + (x_add * index), 10, 65 + (x_add * (index + 1)), 10 + ((score) * 30)), fill = "#FFFFFF")
        index += 1
    
    draw.rectangle((65, 10, 65 + width, 10), "#FF0000")
    draw.rectangle((65, 40, 65 + width, 40), "#FF0000")
    draw.rectangle((65, 10, 65, 40), "#FF0000")
    draw.rectangle((65 + width, 10, 65 + width, 40), "#FF0000")        
    draw.rectangle((66, 25, 64 + width, 25), "#0094FF")
    
    draw.text((50, 130), "White (" + str(round(player_accuracy(white), 1)) + "%)", "#FFFFFF")

    draw.text((50, 150), "Best Move: " + str(white[MoveRate.BestMove]), determine_color(MoveRate.BestMove))
    draw.text((50, 150 + (15 * 1)), "Excellent Move: " + str(white[MoveRate.Excellent]), determine_color(MoveRate.Excellent))
    draw.text((50, 150 + (15 * 2)), "Good Move: " + str(white[MoveRate.Good]), determine_color(MoveRate.Good))
    draw.text((50, 150 + (15 * 3)), "Inaccuracy: " + str(white[MoveRate.Inaccuracy]), determine_color(MoveRate.Inaccuracy))
    draw.text((50, 150 + (15 * 4)), "Mistake: " + str(white[MoveRate.Mistake]), determine_color(MoveRate.Mistake))
    draw.text((50, 150 + (15 * 5)), "Blunder: " + str(white[MoveRate.Blunder]), determine_color(MoveRate.Blunder))
    draw.text((50, 150 + (15 * 6)), "Miss: " + str(white[MoveRate.Miss]), determine_color(MoveRate.Miss))
    draw.text((50, 150 + (15 * 7)), "Brilliant Move: " + str(white[MoveRate.Brilliant]), determine_color(MoveRate.Brilliant))
    draw.text((50, 150 + (15 * 8)), "Great Move: " + str(white[MoveRate.GreatMove]), determine_color(MoveRate.GreatMove))

    draw.text((250, 130), "Black (" + str(round(player_accuracy(black), 1)) + "%)", "#FFFFFF")

    draw.text((250, 150), "Best Move: " + str(black[MoveRate.BestMove]), determine_color(MoveRate.BestMove))
    draw.text((250, 150 + (15 * 1)), "Excellent Move: " + str(black[MoveRate.Excellent]), determine_color(MoveRate.Excellent))
    draw.text((250, 150 + (15 * 2)), "Good Move: " + str(black[MoveRate.Good]), determine_color(MoveRate.Good))
    draw.text((250, 150 + (15 * 3)), "Inaccuracy: " + str(black[MoveRate.Inaccuracy]), determine_color(MoveRate.Inaccuracy))
    draw.text((250, 150 + (15 * 4)), "Mistake: " + str(black[MoveRate.Mistake]), determine_color(MoveRate.Mistake))
    draw.text((250, 150 + (15 * 5)), "Blunder: " + str(black[MoveRate.Blunder]), determine_color(MoveRate.Blunder))
    draw.text((250, 150 + (15 * 6)), "Miss: " + str(black[MoveRate.Miss]), determine_color(MoveRate.Miss))
    draw.text((250, 150 + (15 * 7)), "Brilliant Move: " + str(black[MoveRate.Brilliant]), determine_color(MoveRate.Brilliant))
    draw.text((250, 150 + (15 * 8)), "Great Move: " + str(black[MoveRate.GreatMove]), determine_color(MoveRate.GreatMove))

    for _ in range(5):
        images.append(image)
    image.save("output-review.png")

    print("Saving gif...")
    images[0].save("output.gif", save_all = True, append_images = images[1:], duration = 2500, loop = 0)
    print("Done!")


if __name__ == "__main__":
    main()