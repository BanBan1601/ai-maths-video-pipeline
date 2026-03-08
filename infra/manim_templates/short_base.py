from manim import *


class VerticalShortBase(Scene):
    def construct(self):
        title = Text("Maths Short Template").scale(0.7)
        subtitle = Text("Hook • Intuition • Precision • Payoff").scale(0.4).next_to(title, DOWN, buff=0.3)
        group = VGroup(title, subtitle).arrange(DOWN, buff=0.25)
        self.play(FadeIn(group))
        self.wait(1)
