"""Non-consuming exits shared by independent task entry flows."""


def exploration_list_exit(screen):
    title = screen.find('探险队伍一览', (250, 15, 710, 65), exact=True)
    close = screen.find('关闭', (350, 440, 615, 520), exact=True)
    return close if title and close and min(title.score, close.score) >= .95 else None


def battle_result_exit(screen):
    """A task stopped on a settled result; the battle cost is already decided."""
    total = screen.find('伤害合计', (35, 0, 160, 42), exact=True)
    report = screen.find('伤害报告', (790, 15, 945, 65), exact=True)
    following = screen.find('下一步', (740, 455, 920, 525), exact=True)
    return following if total and report and following and min(total.score, report.score, following.score) >= .95 else None
