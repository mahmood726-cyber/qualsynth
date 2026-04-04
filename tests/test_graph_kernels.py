import pytest
import math
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.graph_kernels import analyse_graph_kernels


@pytest.fixture
def kernel_studies():
    """Studies with overlapping theme assignments for kernel analysis."""
    studies = [
        StudyInput(study_id="S1", title="Study A", authors="A", year=2020,
                   key_findings=["finding one"]),
        StudyInput(study_id="S2", title="Study B", authors="B", year=2021,
                   key_findings=["finding two"]),
        StudyInput(study_id="S3", title="Study C", authors="C", year=2022,
                   key_findings=["finding three"]),
        StudyInput(study_id="S4", title="Study D", authors="D", year=2023,
                   key_findings=["finding four"]),
    ]
    themes = [
        Theme(theme_id="T1", label="Theme alpha",
              assigned_studies=["S1", "S2", "S3"]),
        Theme(theme_id="T2", label="Theme beta",
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T3", label="Theme gamma",
              assigned_studies=["S2", "S3", "S4"]),
    ]
    return studies, themes


def test_wl_kernel_symmetric(kernel_studies):
    """WL kernel matrix must be symmetric."""
    studies, themes = kernel_studies
    result = analyse_graph_kernels(studies, themes)
    K = result["wl_kernel_matrix"]
    n = len(studies)
    for i in range(n):
        for j in range(n):
            assert abs(K[i][j] - K[j][i]) < 1e-9, (
                f"WL kernel not symmetric at ({i},{j}): {K[i][j]} != {K[j][i]}"
            )


def test_rw_kernel_symmetric(kernel_studies):
    """Random walk kernel matrix must be symmetric."""
    studies, themes = kernel_studies
    result = analyse_graph_kernels(studies, themes)
    K = result["rw_kernel_matrix"]
    n = len(studies)
    for i in range(n):
        for j in range(n):
            assert abs(K[i][j] - K[j][i]) < 1e-9, (
                f"RW kernel not symmetric at ({i},{j}): {K[i][j]} != {K[j][i]}"
            )


def test_kernel_pca_coords_all_studies(kernel_studies):
    """Kernel PCA must return coordinates for all studies."""
    studies, themes = kernel_studies
    result = analyse_graph_kernels(studies, themes)
    for s in studies:
        assert s.study_id in result["kernel_pca_coords"], (
            f"Missing PCA coords for {s.study_id}"
        )
        coords = result["kernel_pca_coords"][s.study_id]
        assert len(coords) == 2, f"Expected 2D coords, got {len(coords)}D"


def test_normalized_similarity_diagonal(kernel_studies):
    """Diagonal of normalized similarity should be 1.0 (for non-isolated studies)."""
    studies, themes = kernel_studies
    result = analyse_graph_kernels(studies, themes)
    norm = result["normalized_similarity"]
    for i in range(len(studies)):
        # Only check if the study has a non-zero kernel value
        if result["wl_kernel_matrix"][i][i] > 0:
            assert abs(norm[i][i] - 1.0) < 1e-9, (
                f"Normalized diagonal [{i}] = {norm[i][i]}, expected 1.0"
            )


def test_normalized_similarity_range(kernel_studies):
    """Normalized similarity values must be in [0, 1] (non-negative kernels)."""
    studies, themes = kernel_studies
    result = analyse_graph_kernels(studies, themes)
    norm = result["normalized_similarity"]
    n = len(studies)
    for i in range(n):
        for j in range(n):
            assert -1e-9 <= norm[i][j] <= 1.0 + 1e-9, (
                f"Normalized similarity [{i}][{j}] = {norm[i][j]} out of range"
            )
