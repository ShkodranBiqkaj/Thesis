import pytest
import pygame

class DummySurface:
    def get_width(self):
        return 40

    def get_height(self):
        return 40

    def convert_alpha(self):
        return self

def stub_load(path, *args, **kwargs):
    """Stub for pygame.image.load"""
    return DummySurface()

def stub_scale(surface, size, *args, **kwargs):
    """Stub for pygame.transform.scale"""
    return surface

@pytest.fixture(autouse=True)
def dummy_pygame(monkeypatch):
    monkeypatch.setattr(pygame.image, 'load', stub_load)
    monkeypatch.setattr(pygame.transform, 'scale', stub_scale)