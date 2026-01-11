#!/usr/bin/env python3
import sys, threading
from engine import Engine

def main():
    eng = Engine()

    while True:
        line = sys.stdin.readline()
        if not line: break

        try:
            args = line.strip().split()
            if not args: continue

            command = args[0].lower()

            if command == "uci":
                eng.send("id name Débâcle 1.0")
                eng.send("id author satryraz")
                eng.send("uciok")
            elif command == "isready":
                eng.send("readyok")
            elif command == "position":
                if eng.is_searching:
                    # position changée! stop search
                    eng.stop_signal = True
                eng.set_pos(args)
            elif command == "go":
                if eng.is_searching:
                    # recommencer recherche!
                    eng.stop_signal = True
                eng.start_search(args)
            elif command == "stop":
                eng.stop_signal = True
            elif command == "quit":
                eng.stop_signal = True
                break
        except Exception as e:
            eng.send(f"info string critical engine error: {e}")

if __name__ == "__main__":
    main()
