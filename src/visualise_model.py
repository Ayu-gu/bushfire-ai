import matplotlib.pyplot as plt


# -----------------------------------
# MODEL ARCHITECTURE
# -----------------------------------

layers = [
    ("Input\nFeatures", 15),
    ("Hidden\nLayer 1", 32),
    ("Hidden\nLayer 2", 16),
    ("Hidden\nLayer 3", 8),
    ("Output\nRisk", 1),
]


def visualise_architecture():

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    ax.axis("off")

    x_positions = range(len(layers))

    for x, (name, neurons) in zip(
        x_positions,
        layers
    ):

        # We don't draw all 32 neurons because
        # it would become visually messy.
        visible_neurons = min(neurons, 10)

        spacing = 0.7

        start_y = (
            -(visible_neurons - 1)
            * spacing
            / 2
        )

        for i in range(visible_neurons):

            y = start_y + i * spacing

            circle = plt.Circle(
                (x * 3, y),
                0.18,
                fill=False,
                linewidth=2
            )

            ax.add_patch(circle)

        # Show ... when layer contains
        # more neurons than we draw.
        if neurons > visible_neurons:

            ax.text(
                x * 3,
                start_y - 0.6,
                "...",
                ha="center",
                fontsize=16
            )

        ax.text(
            x * 3,
            start_y - 1.4,
            f"{name}\n{neurons} neurons",
            ha="center",
            fontsize=11,
            fontweight="bold"
        )

    # Connections between layers
    for layer_index in range(
        len(layers) - 1
    ):

        x1 = layer_index * 3
        x2 = (layer_index + 1) * 3

        neurons1 = min(
            layers[layer_index][1],
            10
        )

        neurons2 = min(
            layers[layer_index + 1][1],
            10
        )

        spacing = 0.7

        start1 = (
            -(neurons1 - 1)
            * spacing
            / 2
        )

        start2 = (
            -(neurons2 - 1)
            * spacing
            / 2
        )

        for i in range(neurons1):

            for j in range(neurons2):

                y1 = start1 + i * spacing
                y2 = start2 + j * spacing

                ax.plot(
                    [x1 + 0.18, x2 - 0.18],
                    [y1, y2],
                    linewidth=0.25,
                    alpha=0.25
                )

    ax.set_xlim(-1, 13)
    ax.set_ylim(-6, 5)

    ax.set_title(
        "Bushfire AI v0.4 — Neural Network Architecture",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    visualise_architecture()