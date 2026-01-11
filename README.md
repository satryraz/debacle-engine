# debacle-engine / Débâcle
un moteur d'échecs UCI fait en Python avec la librarie [bulletchess](https://bulletchess.info/)

> le nom "Débâcle" a été choisi car c'est un peu un synonyme du mot "Échec"

[voir mon bot jouer sur lichess!](https://lichess.org/@/debacle-engine)

### moteur
- [x] negamax avec alpha-beta, ordonnancement mvv-lva&pv-move, et quiescence
- [x] recherche itérative avec time management basique (time/20 + inc/2)
- [x] table de transposition avec zobrist hashing des positions
- [x] évaluation basique avec piece-square tables tirées approx. d'[ici](https://www.chessprogramming.org/Simplified_Evaluation_Function)
- [x] interface UCI basique avec threading pour ne pas se bloquer

### installation & build
* prérequis : python 3.14+ (voir requirements.txt)
```
pip install -r requirements.txt
```
* pour générer un exécutable avec UCI (compilation avec Nuitka) :
```bash
chmod +x build.sh
./build.sh
```

### remerciements
au club de maths d'Orsay, au [chess programming wiki](https://www.chessprogramming.org/Main_Page) et à [sebastian lague](https://www.youtube.com/c/SebastianLague)

### license
GNU GPL v3 (voir le fichier LICENSE)
