# GitHubへのプッシュ手順

## ステップ1: Gitリポジトリの初期化

```bash
cd "/Users/momokaiwasaki/Documents/AIエンジニア講座/5-4-2_Dify 実践課題②"
git init
```

## ステップ2: ファイルをステージング

```bash
git add .
```

**注意**: `.env`ファイルは`.gitignore`に含まれているため、コミットされません。

## ステップ3: 初回コミット

```bash
git commit -m "Initial commit: LINE × Dify Chat Bot連携プロジェクト"
```

## ステップ4: GitHubでリポジトリを作成

1. [GitHub](https://github.com) にログイン
2. 右上の「+」ボタンをクリック → 「New repository」を選択
3. リポジトリ名を入力（例: `line-dify-chatbot`）
4. 「Public」または「Private」を選択
5. 「Initialize this repository with a README」のチェックを**外す**（既にREADMEがあるため）
6. 「Create repository」をクリック

## ステップ5: リモートリポジトリを追加

GitHubで作成したリポジトリのURLをコピーして、以下を実行：

```bash
git remote add origin https://github.com/your-username/your-repo-name.git
```

**例:**
```bash
git remote add origin https://github.com/username/line-dify-chatbot.git
```

## ステップ6: ブランチ名を設定（必要に応じて）

```bash
git branch -M main
```

## ステップ7: プッシュ

```bash
git push -u origin main
```

## 確認

GitHubのリポジトリページを開いて、ファイルがアップロードされているか確認してください。

## 注意事項

- `.env`ファイルは`.gitignore`に含まれているため、コミットされません
- API Keyやトークンなどの機密情報はGitHubにアップロードされません
- 必要に応じて`.env.example`ファイルをコミットして、他の人が設定できるようにしてください

