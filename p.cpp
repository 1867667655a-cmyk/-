#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <random>
#include <ctime>
#include <fstream> // 用于文件读写

using namespace std;

// === 基础定义 ===
enum Suit { CLUBS, DIAMONDS, HEARTS, SPADES };
enum Rank { TWO = 2, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING, ACE };

const string MONEY_FILE = "money.txt"; // 存档文件名

// === 扑克牌类 ===
struct Card {
    Suit suit;
    Rank rank;

    int getValue() const {
        if (rank >= TWO && rank <= TEN) return static_cast<int>(rank);
        if (rank >= JACK && rank <= KING) return 10;
        return 11; 
    }

    string toString() const {
        string rankStr;
        switch (rank) {
            case JACK: rankStr = "J"; break;
            case QUEEN: rankStr = "Q"; break;
            case KING: rankStr = "K"; break;
            case ACE: rankStr = "A"; break;
            default: rankStr = to_string(static_cast<int>(rank)); break;
        }
        string suitStr;
        switch (suit) {
            case CLUBS: suitStr = "梅花"; break;
            case DIAMONDS: suitStr = "方块"; break;
            case HEARTS: suitStr = "红桃"; break;
            case SPADES: suitStr = "黑桃"; break;
        }
        return suitStr + rankStr;
    }
};

// === 资金管理类 ===
class Bank {
private:
    long long balance;

public:
    Bank() : balance(0) {}

    // 从文件加载余额
    void loadMoney() {
        ifstream inFile(MONEY_FILE);
        if (inFile.is_open()) {
            inFile >> balance;
            inFile.close();
        } else {
            // 如果文件不存在，默认给1000
            balance = 1000;
            saveMoney();
            cout << ">>> 未找到存档，已创建新账户，初始资金: 1000 <<<" << endl;
        }
    }

    // 保存余额到文件
    void saveMoney() {
        ofstream outFile(MONEY_FILE);
        if (outFile.is_open()) {
            outFile << balance;
            outFile.close();
        } else {
            cerr << "错误：无法写入存档文件！" << endl;
        }
    }

    long long getBalance() const {
        return balance;
    }

    // 结算输赢
    void updateBalance(long long amount) {
        balance += amount;
        saveMoney(); // 实时保存
    }
};

// === 牌组类 ===
class Deck {
private:
    vector<Card> cards;
public:
    Deck() {
        init();
    }
    void init() {
        cards.clear();
        for (int s = CLUBS; s <= SPADES; ++s) {
            for (int r = TWO; r <= ACE; ++r) {
                cards.push_back({static_cast<Suit>(s), static_cast<Rank>(r)});
            }
        }
    }
    void shuffle() {
        static mt19937 rng(static_cast<unsigned>(time(0)));
        std::shuffle(cards.begin(), cards.end(), rng);
    }
    Card deal() {
        Card c = cards.back();
        cards.pop_back();
        return c;
    }
    void checkDeck() {
        if (cards.size() < 10) {
            init();
            shuffle();
            cout << ">>> 牌堆已重新洗牌 <<<" << endl;
        }
    }
};

// === 手牌类 ===
class Hand {
public:
    vector<Card> cards;

    void addCard(Card c) {
        cards.push_back(c);
    }
    void clear() {
        cards.clear();
    }
    int getScore() const {
        int score = 0;
        int aceCount = 0;
        for (const auto& card : cards) {
            score += card.getValue();
            if (card.rank == ACE) aceCount++;
        }
        while (score > 21 && aceCount > 0) {
            score -= 10;
            aceCount--;
        }
        return score;
    }
    void printHand(bool hideFirstCard = false) const {
        for (size_t i = 0; i < cards.size(); ++i) {
            if (i == 0 && hideFirstCard) {
                cout << "[ ?? ] ";
            } else {
                cout << "[" << cards[i].toString() << "] ";
            }
        }
        if (!hideFirstCard) {
            cout << " -> 点数: " << getScore();
        }
        cout << endl;
    }
};

// === 游戏主逻辑 ===
void playBlackjack() {
    Bank bank;
    bank.loadMoney(); // 启动时读取

    Deck deck;
    deck.shuffle();
    Hand playerHand;
    Hand dealerHand;
    
    char playAgain = 'y';

    while (playAgain == 'y' || playAgain == 'Y') {
        // 1. 检查资金
        long long currentMoney = bank.getBalance();
        if (currentMoney <= 0) {
            cout << "\n===================================" << endl;
            cout << " 你的余额为 0，无法继续游戏！" << endl;
            cout << " 请手动修改 " << MONEY_FILE << " 进行充值。" << endl;
            cout << "===================================" << endl;
            break;
        }

        deck.checkDeck();
        playerHand.clear();
        dealerHand.clear();

        // 2. 下注环节
        long long betAmount = 0;
        cout << "\n===================================" << endl;
        cout << " 当前持有资金: " << currentMoney << endl;
        cout << "===================================" << endl;
        
        while (true) {
            cout << "请输入下注金额: ";
            if (!(cin >> betAmount)) {
                cin.clear(); cin.ignore(1000, '\n'); 
                continue; 
            }
            if (betAmount <= 0) {
                cout << "下注金额必须大于 0。" << endl;
            } else if (betAmount > currentMoney) {
                cout << "余额不足！最大可下注: " << currentMoney << endl;
            } else {
                break;
            }
        }

        // 3. 初始发牌
        bool hasSwapped = false;
        playerHand.addCard(deck.deal());
        dealerHand.addCard(deck.deal()); 
        playerHand.addCard(deck.deal());
        dealerHand.addCard(deck.deal());

        // 4. 玩家回合
        bool playerBusted = false;
        while (true) {
            cout << "\n庄家的牌: ";
            dealerHand.printHand(true);
            cout << "你的牌: ";
            playerHand.printHand();

            if (playerHand.getScore() == 21) {
                cout << "\n*** 黑杰克！21点！ ***" << endl;
                break; 
            }

            cout << "\n[H] 拿牌 | [P] 停牌";
            if (!hasSwapped) cout << " | [S] 交换暗牌(一次)";
            cout << "\n指令: ";

            char choice;
            cin >> choice;

            if (choice == 'h' || choice == 'H') {
                Card newCard = deck.deal();
                cout << ">> 摸牌: " << newCard.toString() << endl;
                playerHand.addCard(newCard);
                if (playerHand.getScore() > 21) {
                    cout << "你的牌: ";
                    playerHand.printHand();
                    cout << "\n--> 爆牌了！(Bust) <--" << endl;
                    playerBusted = true;
                    break;
                }
            }
            else if (choice == 'p' || choice == 'P') {
                break;
            }
            else if ((choice == 's' || choice == 'S') && !hasSwapped) {
                std::swap(playerHand.cards[0], dealerHand.cards[0]);
                hasSwapped = true;
                cout << "\n>>> 发动技能：交换了庄家的暗牌！ <<<" << endl;
                continue; 
            }
            else {
                cout << "无效指令。" << endl;
            }
        }

        // 5. 庄家回合
        if (!playerBusted) {
            cout << "\n--- 庄家回合 ---" << endl;
            cout << "庄家亮牌: ";
            dealerHand.printHand(); 

            while (dealerHand.getScore() < 17) {
                cout << "庄家拿牌..." << endl;
                Card newCard = deck.deal();
                cout << "庄家摸到: " << newCard.toString() << endl;
                dealerHand.addCard(newCard);
                cout << "庄家牌面: ";
                dealerHand.printHand();
            }
        }

        // 6. 结算与奖惩逻辑
        int playerScore = playerHand.getScore();
        int dealerScore = dealerHand.getScore();

        cout << "\n================ 结算 ================" << endl;
        cout << "你的点数: " << playerScore << endl;
        if (!playerBusted) cout << "庄家点数: " << dealerScore << endl;

        long long winAmount = 0;
        string resultMsg = "";

        if (playerBusted) {
            // 玩家爆牌：输掉底注
            winAmount = -betAmount;
            resultMsg = "你爆牌了，输掉筹码: " + to_string(betAmount);
        }
        else if (dealerScore > 21) {
            // 庄家爆牌：玩家赢
            // 根据规则：如果玩家此时正好21点，赢双倍；否则赢单倍
            if (playerScore == 21) {
                winAmount = betAmount * 2;
                resultMsg = "庄家爆牌且你持有21点！双倍胜利！赢得: " + to_string(winAmount);
            } else {
                winAmount = betAmount;
                resultMsg = "庄家爆牌！你赢了: " + to_string(winAmount);
            }
        }
        else {
            // 双方都没爆牌，比大小
            if (playerScore > dealerScore) {
                if (playerScore == 21) {
                    winAmount = betAmount * 2;
                    resultMsg = "21点绝杀！双倍胜利！赢得: " + to_string(winAmount);
                } else {
                    winAmount = betAmount;
                    resultMsg = "你点数较大！赢得: " + to_string(winAmount);
                }
            } 
            else if (playerScore < dealerScore) {
                if (dealerScore == 21) {
                    winAmount = -(betAmount * 2);
                    resultMsg = "庄家拿到21点！双倍惩罚！输掉: " + to_string(-winAmount);
                } else {
                    winAmount = -betAmount;
                    resultMsg = "你输了: " + to_string(-winAmount);
                }
            } 
            else {
                // 平局 (Push)
                winAmount = 0;
                resultMsg = "平局！筹码退回。";
            }
        }

        cout << resultMsg << endl;
        bank.updateBalance(winAmount);
        cout << "当前余额: " << bank.getBalance() << endl;
        cout << "--------------------------------------" << endl;

        if (bank.getBalance() <= 0) {
            cout << "\n你已经破产了！游戏结束。" << endl;
            break;
        }

        cout << "\n是否继续? (y/n): ";
        cin >> playAgain;
    }
    cout << "退出游戏，资金已保存。" << endl;
}

int main() {
    system("chcp 65001");
	playBlackjack();
	return 0;
    

}

