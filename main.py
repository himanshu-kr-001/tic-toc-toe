import tkinter as tk

from gui_tk import TicTacToeGUI


def main() -> None:
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
