from rest_framework.routers import DefaultRouter
from .views import ContainerViewSet, ZoneViewSet

router = DefaultRouter()
router.register("containers", ContainerViewSet, basename="container")
router.register("zones", ZoneViewSet, basename="zone")

urlpatterns = router.urls
