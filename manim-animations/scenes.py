"""
3Blue1Brown 스타일 수학 애니메이션 예제
Manim Community Edition 사용

실행 방법:
    manim -pql scenes.py SceneName

옵션:
    -p: 렌더링 후 미리보기
    -q: 품질 (l=저화질/빠름, m=중간, h=고화질, k=4K)
"""

from manim import *


# ============================================
# 1. 기본 예제: 원과 사각형 변환
# ============================================
class BasicShapes(Scene):
    """기본 도형 생성 및 변환 애니메이션"""

    def construct(self):
        # 제목
        title = Text("Manim 기본 도형", font_size=48)
        self.play(Write(title))
        self.wait(0.5)
        self.play(title.animate.to_edge(UP))

        # 원 생성
        circle = Circle(radius=1.5, color=BLUE)
        circle.set_fill(BLUE, opacity=0.5)

        self.play(Create(circle))
        self.wait(0.5)

        # 사각형으로 변환
        square = Square(side_length=3, color=GREEN)
        square.set_fill(GREEN, opacity=0.5)

        self.play(Transform(circle, square))
        self.wait(0.5)

        # 삼각형으로 변환
        triangle = Triangle(color=RED)
        triangle.scale(2)
        triangle.set_fill(RED, opacity=0.5)

        self.play(Transform(circle, triangle))
        self.wait()


# ============================================
# 2. 피타고라스 정리 시각화
# ============================================
class PythagoreanTheorem(Scene):
    """피타고라스 정리: a² + b² = c²"""

    def construct(self):
        # 제목
        title = MathTex(r"a^2 + b^2 = c^2", font_size=60)
        title.to_edge(UP)
        self.play(Write(title))

        # 직각삼각형
        a, b = 2, 1.5  # 두 변의 길이
        c = np.sqrt(a**2 + b**2)

        # 삼각형 꼭짓점
        A = ORIGIN
        B = a * RIGHT
        C = a * RIGHT + b * UP

        triangle = Polygon(A, B, C, color=WHITE, stroke_width=3)
        triangle.move_to(ORIGIN)

        self.play(Create(triangle))

        # 각 변에 정사각형 추가
        # a² 정사각형 (아래)
        sq_a = Square(side_length=a, color=BLUE, fill_opacity=0.5)
        sq_a.next_to(triangle, DOWN, buff=0)
        sq_a.align_to(triangle, LEFT)

        label_a = MathTex(r"a^2", color=BLUE)
        label_a.move_to(sq_a)

        # b² 정사각형 (오른쪽)
        sq_b = Square(side_length=b, color=GREEN, fill_opacity=0.5)
        sq_b.next_to(triangle, RIGHT, buff=0)
        sq_b.align_to(triangle, DOWN)

        label_b = MathTex(r"b^2", color=GREEN)
        label_b.move_to(sq_b)

        # c² 정사각형 (빗변)
        sq_c = Square(side_length=c, color=RED, fill_opacity=0.5)
        sq_c.rotate(np.arctan(b/a))
        sq_c.move_to(triangle.get_center() + 1.5*LEFT + 0.5*UP)

        label_c = MathTex(r"c^2", color=RED)
        label_c.move_to(sq_c)

        # 애니메이션
        self.play(
            FadeIn(sq_a), Write(label_a),
            FadeIn(sq_b), Write(label_b),
        )
        self.wait(0.5)

        self.play(FadeIn(sq_c), Write(label_c))
        self.wait()

        # 결론 강조
        conclusion = MathTex(
            r"\text{면적: }", r"a^2", r"+", r"b^2", r"=", r"c^2",
            font_size=48
        )
        conclusion[1].set_color(BLUE)
        conclusion[3].set_color(GREEN)
        conclusion[5].set_color(RED)
        conclusion.to_edge(DOWN)

        self.play(Write(conclusion))
        self.wait()


# ============================================
# 3. 미적분 시각화: 함수의 미분
# ============================================
class DerivativeVisualization(Scene):
    """함수의 미분 - 접선의 기울기"""

    def construct(self):
        # 좌표축
        axes = Axes(
            x_range=[-1, 5, 1],
            y_range=[-1, 10, 2],
            x_length=8,
            y_length=6,
            axis_config={"include_tip": True},
        )
        labels = axes.get_axis_labels(x_label="x", y_label="f(x)")

        # 함수 f(x) = x²
        func = axes.plot(lambda x: x**2, color=BLUE, x_range=[0, 3])
        func_label = MathTex(r"f(x) = x^2", color=BLUE)
        func_label.to_corner(UR)

        self.play(Create(axes), Write(labels))
        self.play(Create(func), Write(func_label))

        # 점과 접선
        x_tracker = ValueTracker(0.5)

        dot = always_redraw(
            lambda: Dot(
                axes.c2p(x_tracker.get_value(), x_tracker.get_value()**2),
                color=YELLOW
            )
        )

        def get_tangent_line():
            x = x_tracker.get_value()
            slope = 2 * x  # f'(x) = 2x

            tangent = axes.plot(
                lambda t: slope * (t - x) + x**2,
                x_range=[max(0, x-1), min(3, x+1)],
                color=RED
            )
            return tangent

        tangent = always_redraw(get_tangent_line)

        # 기울기 표시
        slope_text = always_redraw(
            lambda: MathTex(
                rf"f'({x_tracker.get_value():.1f}) = {2*x_tracker.get_value():.1f}",
                color=RED
            ).to_corner(UL)
        )

        self.play(Create(dot), Create(tangent), Write(slope_text))

        # 점 이동 애니메이션
        self.play(x_tracker.animate.set_value(2.5), run_time=4, rate_func=smooth)
        self.wait()

        # 미분 공식
        derivative = MathTex(r"f'(x) = 2x", font_size=48, color=GREEN)
        derivative.to_edge(DOWN)
        self.play(Write(derivative))
        self.wait()


# ============================================
# 4. 푸리에 급수 시각화
# ============================================
class FourierSeries(Scene):
    """사각파의 푸리에 급수 근사"""

    def construct(self):
        title = Text("푸리에 급수: 사각파 근사", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        axes = Axes(
            x_range=[-PI, PI, PI/2],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=4,
        )
        axes.shift(DOWN * 0.5)

        self.play(Create(axes))

        # 사각파 (목표)
        def square_wave(x):
            return 1 if x > 0 else (-1 if x < 0 else 0)

        target = axes.plot(
            square_wave,
            x_range=[-PI + 0.01, PI - 0.01],
            discontinuities=[0],
            color=YELLOW,
            stroke_width=2,
        )
        target_label = Text("목표: 사각파", font_size=24, color=YELLOW)
        target_label.next_to(axes, RIGHT)

        self.play(Create(target), Write(target_label))

        # 푸리에 급수 근사
        def fourier_approx(n_terms):
            def f(x):
                result = 0
                for k in range(1, n_terms + 1, 2):  # 홀수만
                    result += (4 / (PI * k)) * np.sin(k * x)
                return result
            return f

        approx_graph = None
        terms_label = None

        for n in [1, 3, 5, 9, 15, 25]:
            new_graph = axes.plot(
                fourier_approx(n),
                x_range=[-PI, PI],
                color=BLUE,
            )
            new_label = MathTex(
                rf"n = {n} \text{{ 항}}",
                font_size=32, color=BLUE
            )
            new_label.next_to(axes, LEFT)

            if approx_graph is None:
                self.play(Create(new_graph), Write(new_label))
            else:
                self.play(
                    Transform(approx_graph, new_graph),
                    Transform(terms_label, new_label),
                )

            approx_graph = new_graph if approx_graph is None else approx_graph
            terms_label = new_label if terms_label is None else terms_label
            self.wait(0.5)

        # 수식
        formula = MathTex(
            r"f(x) = \frac{4}{\pi} \sum_{k=1,3,5,...}^{\infty} \frac{\sin(kx)}{k}",
            font_size=36
        )
        formula.to_edge(DOWN)
        self.play(Write(formula))
        self.wait()


# ============================================
# 5. 3D 표면 그래프
# ============================================
class Surface3D(ThreeDScene):
    """3D 표면 시각화"""

    def construct(self):
        # 제목
        title = Text("3D 표면: z = sin(x)cos(y)", font_size=36)
        title.to_corner(UL)
        title.fix_in_frame()

        # 3D 좌표축
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-1.5, 1.5, 0.5],
        )

        # 표면 함수
        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(30, 30),
            fill_opacity=0.8,
        )
        surface.set_style(fill_opacity=0.7)
        surface.set_fill_by_value(
            axes=axes,
            colorscale=[(RED, -1), (YELLOW, 0), (GREEN, 1)],
            axis=2
        )

        # 카메라 설정
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

        self.add_fixed_in_frame_mobjects(title)
        self.play(Write(title))
        self.play(Create(axes))
        self.play(Create(surface), run_time=2)

        # 카메라 회전
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()
        self.wait()


# ============================================
# 6. 뉴럴 네트워크 시각화
# ============================================
class NeuralNetwork(Scene):
    """간단한 뉴럴 네트워크 구조"""

    def construct(self):
        title = Text("Neural Network", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))

        # 레이어 구조
        layers = [4, 6, 6, 2]  # 각 레이어의 노드 수
        layer_spacing = 2.5
        node_radius = 0.2

        all_nodes = []
        all_edges = []

        # 노드 생성
        for i, n_nodes in enumerate(layers):
            layer_nodes = []
            x = (i - len(layers)/2 + 0.5) * layer_spacing

            for j in range(n_nodes):
                y = (j - n_nodes/2 + 0.5) * 0.8
                node = Circle(radius=node_radius, color=BLUE)
                node.set_fill(BLUE, opacity=0.8)
                node.move_to([x, y, 0])
                layer_nodes.append(node)

            all_nodes.append(layer_nodes)

        # 엣지 생성
        for i in range(len(all_nodes) - 1):
            for node1 in all_nodes[i]:
                for node2 in all_nodes[i + 1]:
                    edge = Line(
                        node1.get_center(),
                        node2.get_center(),
                        stroke_width=1,
                        color=GRAY,
                        stroke_opacity=0.5
                    )
                    all_edges.append(edge)

        # 애니메이션
        # 먼저 엣지
        self.play(*[Create(edge) for edge in all_edges], run_time=1)

        # 레이어별로 노드 생성
        layer_labels = ["Input", "Hidden 1", "Hidden 2", "Output"]
        for i, (layer_nodes, label) in enumerate(zip(all_nodes, layer_labels)):
            x = (i - len(layers)/2 + 0.5) * layer_spacing
            layer_text = Text(label, font_size=20)
            layer_text.move_to([x, -3, 0])

            self.play(
                *[FadeIn(node) for node in layer_nodes],
                Write(layer_text),
                run_time=0.5
            )

        self.wait()

        # 신호 전파 애니메이션
        for _ in range(2):
            for i in range(len(all_nodes) - 1):
                highlights = []
                for node in all_nodes[i]:
                    highlight = node.copy()
                    highlight.set_color(YELLOW)
                    highlight.scale(1.3)
                    highlights.append(highlight)

                self.play(
                    *[FadeIn(h, scale=0.5) for h in highlights],
                    run_time=0.3
                )
                self.play(
                    *[FadeOut(h) for h in highlights],
                    run_time=0.3
                )

        self.wait()


# ============================================
# 7. 정렬 알고리즘 시각화
# ============================================
class BubbleSort(Scene):
    """버블 정렬 시각화"""

    def construct(self):
        title = Text("Bubble Sort", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))

        # 데이터
        data = [5, 2, 8, 1, 9, 3, 7, 4, 6]
        n = len(data)

        # 막대 생성
        bars = VGroup()
        bar_width = 0.6
        spacing = 0.8

        def create_bars(values):
            bars = VGroup()
            for i, val in enumerate(values):
                bar = Rectangle(
                    width=bar_width,
                    height=val * 0.4,
                    fill_opacity=0.8,
                    color=BLUE
                )
                bar.move_to([
                    (i - n/2 + 0.5) * spacing,
                    val * 0.2 - 2,
                    0
                ])

                label = Text(str(val), font_size=20)
                label.next_to(bar, UP, buff=0.1)

                group = VGroup(bar, label)
                bars.add(group)
            return bars

        bars = create_bars(data)
        self.play(FadeIn(bars))
        self.wait(0.5)

        # 버블 정렬 애니메이션
        for i in range(n):
            for j in range(n - i - 1):
                # 비교 중인 요소 강조
                bars[j][0].set_color(YELLOW)
                bars[j+1][0].set_color(YELLOW)
                self.wait(0.2)

                if data[j] > data[j + 1]:
                    # 교환
                    data[j], data[j + 1] = data[j + 1], data[j]

                    self.play(
                        bars[j].animate.shift(RIGHT * spacing),
                        bars[j+1].animate.shift(LEFT * spacing),
                        run_time=0.3
                    )
                    bars[j], bars[j+1] = bars[j+1], bars[j]

                # 색상 복원
                bars[j][0].set_color(BLUE)
                bars[j+1][0].set_color(BLUE)

            # 정렬 완료된 요소
            bars[n-i-1][0].set_color(GREEN)

        # 첫 번째 요소도 완료 표시
        bars[0][0].set_color(GREEN)

        complete = Text("정렬 완료!", font_size=36, color=GREEN)
        complete.to_edge(DOWN)
        self.play(Write(complete))
        self.wait()


# ============================================
# 8. 오일러 공식 시각화
# ============================================
class EulerFormula(Scene):
    """오일러 공식: e^(iπ) + 1 = 0"""

    def construct(self):
        # 제목
        title = MathTex(r"e^{i\pi} + 1 = 0", font_size=72)
        subtitle = Text("세상에서 가장 아름다운 수식", font_size=24)
        subtitle.next_to(title, DOWN)

        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait()

        self.play(FadeOut(title), FadeOut(subtitle))

        # 복소 평면
        plane = ComplexPlane(
            x_range=[-2, 2, 1],
            y_range=[-2, 2, 1],
            x_length=6,
            y_length=6,
        )
        plane.add_coordinates()

        self.play(Create(plane))

        # 단위원
        circle = Circle(radius=plane.get_x_unit_size(), color=BLUE)
        self.play(Create(circle))

        # e^(iθ) 점 추적
        theta_tracker = ValueTracker(0)

        dot = always_redraw(
            lambda: Dot(
                plane.n2p(np.exp(1j * theta_tracker.get_value())),
                color=YELLOW
            )
        )

        line = always_redraw(
            lambda: Line(
                plane.n2p(0),
                plane.n2p(np.exp(1j * theta_tracker.get_value())),
                color=YELLOW
            )
        )

        angle_label = always_redraw(
            lambda: MathTex(
                rf"\theta = {theta_tracker.get_value():.2f}",
                font_size=32
            ).to_corner(UR)
        )

        self.play(Create(dot), Create(line), Write(angle_label))

        # θ = 0에서 π까지 회전
        self.play(
            theta_tracker.animate.set_value(PI),
            run_time=4,
            rate_func=smooth
        )

        # e^(iπ) = -1 강조
        result = MathTex(r"e^{i\pi} = -1", font_size=48, color=GREEN)
        result.to_edge(DOWN)
        self.play(Write(result))

        self.wait()

        # 최종 공식
        final = MathTex(
            r"e^{i\pi} + 1 = 0",
            font_size=60,
            color=GOLD
        )
        final.move_to(ORIGIN + UP * 2.5)

        self.play(
            FadeOut(result),
            Write(final)
        )
        self.wait(2)
