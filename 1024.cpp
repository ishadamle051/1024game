#include <iomanip>
#include <iostream>
#include <ctime>
#include <cstdlib>

using namespace std;

const int GRID_SIZE = 4;

int grid[GRID_SIZE][GRID_SIZE];
bool merged[GRID_SIZE][GRID_SIZE]; // Track merged status for each tile

void initializeGrid() {
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 0; j < GRID_SIZE; j++) {
            grid[i][j] = 0;
            merged[i][j] = false;
        }
    }
}

void spawnNewTile() {
    int x, y;
    do {
        x = rand() % GRID_SIZE;
        y = rand() % GRID_SIZE;
    } while (grid[x][y] != 0);
    grid[x][y] = (rand() % 2 == 0) ? 2 : 4;
}

void resetMerged() {
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 0; j < GRID_SIZE; j++) {
            merged[i][j] = false;
        }
    }
}

bool shiftLeft() {
    bool moved = false;
    resetMerged();
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 1; j < GRID_SIZE; j++) {
            if (grid[i][j] != 0) {
                int k = j;
                while (k > 0 && grid[i][k - 1] == 0) {
                    grid[i][k - 1] = grid[i][k];
                    grid[i][k] = 0;
                    moved = true;
                    k--;
                }
                if (k > 0 && grid[i][k - 1] == grid[i][k] && !merged[i][k - 1]) {
                    grid[i][k - 1] *= 2;
                    merged[i][k - 1] = true;
                    grid[i][k] = 0;
                    moved = true;
                }
            }
        }
    }
    return moved;
}

bool shiftRight() {
    bool moved = false;
    resetMerged();
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = GRID_SIZE - 2; j >= 0; j--) {
            if (grid[i][j] != 0) {
                int k = j;
                while (k < GRID_SIZE - 1 && grid[i][k + 1] == 0) {
                    grid[i][k + 1] = grid[i][k];
                    grid[i][k] = 0;
                    moved = true;
                    k++;
                }
                if (k < GRID_SIZE - 1 && grid[i][k + 1] == grid[i][k] && !merged[i][k + 1]) {
                    grid[i][k + 1] *= 2;
                    merged[i][k + 1] = true;
                    grid[i][k] = 0;
                    moved = true;
                }
            }
        }
    }
    return moved;
}

bool shiftUp() {
    bool moved = false;
    resetMerged();
    for (int j = 0; j < GRID_SIZE; j++) {
        for (int i = 1; i < GRID_SIZE; i++) {
            if (grid[i][j] != 0) {
                int k = i;
                while (k > 0 && grid[k - 1][j] == 0) {
                    grid[k - 1][j] = grid[k][j];
                    grid[k][j] = 0;
                    moved = true;
                    k--;
                }
                if (k > 0 && grid[k - 1][j] == grid[k][j] && !merged[k - 1][j]) {
                    grid[k - 1][j] *= 2;
                    merged[k - 1][j] = true;
                    grid[k][j] = 0;
                    moved = true;
                }
            }
        }
    }
    return moved;
}

bool shiftDown() {
    bool moved = false;
    resetMerged();
    for (int j = 0; j < GRID_SIZE; j++) {
        for (int i = GRID_SIZE - 2; i >= 0; i--) {
            if (grid[i][j] != 0) {
                int k = i;
                while (k < GRID_SIZE - 1 && grid[k + 1][j] == 0) {
                    grid[k + 1][j] = grid[k][j];
                    grid[k][j] = 0;
                    moved = true;
                    k++;
                }
                if (k < GRID_SIZE - 1 && grid[k + 1][j] == grid[k][j] && !merged[k + 1][j]) {
                    grid[k + 1][j] *= 2;
                    merged[k + 1][j] = true;
                    grid[k][j] = 0;
                    moved = true;
                }
            }
        }
    }
    return moved;
}

bool isGameOver() {
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 0; j < GRID_SIZE; j++) {
            if (grid[i][j] == 0) return false;
            if (i > 0 && grid[i][j] == grid[i - 1][j]) return false;
            if (j > 0 && grid[i][j] == grid[i][j - 1]) return false;
        }
    }
    return true;
}

void printGrid() {
    cout << endl;
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 0; j < GRID_SIZE; j++) {
            if (grid[i][j] == 0) {
                cout << "  . ";
            } else {
                cout << setw(4) << grid[i][j];
            }
        }
        cout << endl;
    }
}

int main() {
    srand(time(NULL));
    initializeGrid();
    spawnNewTile();
    spawnNewTile();

    while (true) {
        printGrid();
        cout << "Enter a direction (l = left, r = right, u = up, d = down): ";
        char direction;
        cin >> direction;

        bool moved = false;
        switch (direction) {
            case 'u':
                moved = shiftUp();
                break;
            case 'l':
                moved = shiftLeft();
                break;
            case 'd':
                moved = shiftDown();
                break;
            case 'r':
                moved = shiftRight();
                break;
            default:
                cout << "Invalid direction." << endl;
                continue;
        }

        if (moved) {
            spawnNewTile();
        }

        if (isGameOver()) {
            printGrid();
            cout << "Game Over!" << endl;
            break;
        }
    }

    return 0;
}
