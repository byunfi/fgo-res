from .FGORes import FGORes
import os


def main(argv=None):
    path = './products/md.sqlite'
    fr = FGORes(path)
    fr.start()
    