

class Category:
    def __init__(self, name):
        self.name = name
        self.ledger = []

    def deposit(self, amount, description=''):
        self.ledger.append({'amount': amount, 'description': description})

    def withdraw(self, amount, description=''):
        if self.check_funds(amount):
            self.ledger.append({'amount': -amount, 'description': description})
            return True
        return False

    def get_balance(self):
        return sum(item['amount'] for item in self.ledger)

    def transfer(self, amount, category):
        if self.check_funds(amount):
            self.withdraw(amount, f'Transfer to {category.name}')
            category.deposit(amount, f'Transfer from {self.name}')
            return True
        return False

    def check_funds(self, amount):
        return amount <= self.get_balance()

    def __str__(self):
        title = self.name.center(30, '*') + '\n'
        items = ''
        for item in self.ledger:
            items += f"{item['description'][:23]:<23}{item['amount']:>7.2f}\n"
        total = f"Total: {self.get_balance():.2f}"
        return title + items + total


def create_spend_chart(categories):
    withdrawals = []
    for cat in categories:
        total = sum(-item['amount'] for item in cat.ledger if item['amount'] < 0)
        withdrawals.append(total)

    total_spent = sum(withdrawals)
    percentages = [int((w / total_spent) * 100) // 10 * 10 for w in withdrawals]

    lines = ['Percentage spent by category']

    for i in range(100, -1, -10):
        line = str(i).rjust(3) + '| '
        for p in percentages:
            line += 'o  ' if p >= i else '   '
        lines.append(line)

    lines.append('    -' + '---' * len(categories))

    max_len = max(len(cat.name) for cat in categories)
    for i in range(max_len):
        line = '     '
        for cat in categories:
            line += (cat.name[i] if i < len(cat.name) else ' ') + '  '
        lines.append(line)

    return '\n'.join(lines)

def create_spend_chart(categories):
    withdrawals = []
    for cat in categories:
        total = sum(-item['amount'] for item in cat.ledger if item['amount'] < 0)
        withdrawals.append(total)

    total_spent = sum(withdrawals)
    
    # --- FIX STARTS HERE ---
    if total_spent == 0:
        return "No spending recorded yet to generate a chart!"
    # --- FIX ENDS HERE ---

    percentages = [int((w / total_spent) * 100) // 10 * 10 for w in withdrawals]

    lines = ['Percentage spent by category']
    for i in range(100, -1, -10):
        line = str(i).rjust(3) + '| '
        for p in percentages:
            line += 'o  ' if p >= i else '   '
        lines.append(line)

    lines.append('    -' + '---' * len(categories))

    max_len = max(len(cat.name) for cat in categories)
    for i in range(max_len):
        line = '     '
        for cat in categories:
            line += (cat.name[i] if i < len(cat.name) else ' ') + '  '
        lines.append(line)

    return '\n'.join(lines)




