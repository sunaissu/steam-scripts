from scripts import check_full_discount_games

def lambda_handler(event, context):
    check_full_discount_games.run()
    return {"status": "done"}
