"""
Client factory for managing document processing clients.

This module provides a singleton factory for creating and managing
all AI provider clients with lazy initialization.

Example:
    from src.services.client_factory import get_client_factory

    factory = get_client_factory()
    mistral = factory.mistral
    openai = factory.openai

    # Health check all
    health = await factory.health_check_all()

    # Cleanup on shutdown
    await factory.cleanup()
"""

from typing import Dict, Any, Optional

from src.services.clients.mistral_client import MistralClient
from src.services.clients.openai_client import OpenAIClient
from src.services.clients.gemini_client import GeminiClient
from src.services.clients.azure_di_client import AzureDIClient
from src.core.logging import get_logger

logger = get_logger(__name__)


class ClientFactory:
    """
    Singleton factory for managing document processing clients.

    Provides lazy initialization of clients - they are only created
    when first accessed. This saves resources and allows the application
    to run even if some API keys are missing.

    Example:
        factory = ClientFactory()

        # Clients created on first access
        mistral = factory.mistral
        openai = factory.openai

        # Health check all active clients
        health = await factory.health_check_all()

        # Cleanup
        await factory.cleanup()
    """

    _instance: Optional["ClientFactory"] = None
    _lock = False

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize factory (only runs once due to singleton)."""
        if self._initialized:
            return

        self._mistral_client: Optional[MistralClient] = None
        self._openai_client: Optional[OpenAIClient] = None
        self._gemini_client: Optional[GeminiClient] = None
        self._azure_di_client: Optional[AzureDIClient] = None

        self._initialized = True

        logger.info("ClientFactory initialized (singleton)")

    @property
    def mistral(self) -> MistralClient:
        """
        Get or create Mistral client (lazy initialization).

        Returns:
            MistralClient: Mistral AI client instance

        Raises:
            ConfigurationError: If Mistral credentials are missing
        """
        if self._mistral_client is None:
            logger.info("Creating Mistral client (lazy initialization)")
            self._mistral_client = MistralClient()
        return self._mistral_client

    @property
    def openai(self) -> OpenAIClient:
        """
        Get or create OpenAI client (lazy initialization).

        Returns:
            OpenAIClient: OpenAI client instance

        Raises:
            ConfigurationError: If OpenAI credentials are missing
        """
        if self._openai_client is None:
            logger.info("Creating OpenAI client (lazy initialization)")
            self._openai_client = OpenAIClient()
        return self._openai_client

    @property
    def gemini(self) -> GeminiClient:
        """
        Get or create Gemini client (lazy initialization).

        Returns:
            GeminiClient: Gemini client instance

        Raises:
            ConfigurationError: If Gemini credentials are missing
        """
        if self._gemini_client is None:
            logger.info("Creating Gemini client (lazy initialization)")
            self._gemini_client = GeminiClient()
        return self._gemini_client

    @property
    def azure_di(self) -> AzureDIClient:
        """
        Get or create Azure DI client (lazy initialization).

        Returns:
            AzureDIClient: Azure Document Intelligence client instance

        Raises:
            ConfigurationError: If Azure DI credentials are missing
        """
        if self._azure_di_client is None:
            logger.info("Creating Azure DI client (lazy initialization)")
            self._azure_di_client = AzureDIClient()
        return self._azure_di_client

    def get_client(self, provider: str):
        """
        Get client by provider name.

        Args:
            provider: Provider name (mistral, openai, gemini, azure_di)

        Returns:
            Client instance for the provider

        Raises:
            ValueError: If provider name is unknown
        """
        provider = provider.lower()

        if provider == "mistral":
            return self.mistral
        elif provider == "openai":
            return self.openai
        elif provider == "gemini":
            return self.gemini
        elif provider in ["azure_di", "azure-di", "azuredi"]:
            return self.azure_di
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: mistral, openai, gemini, azure_di"
            )

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all active clients.

        Only checks clients that have been initialized (lazy loading).

        Returns:
            Dict mapping provider names to health status dicts

        Example:
            {
                "mistral": {"status": "healthy", "latency_ms": 123.45},
                "openai": {"status": "healthy", "latency_ms": 98.76}
            }
        """
        health_results = {}

        if self._mistral_client is not None:
            try:
                health_results["mistral"] = await self._mistral_client.health_check()
            except Exception as e:
                health_results["mistral"] = {
                    "status": "unhealthy",
                    "provider": "mistral",
                    "error": str(e),
                }

        if self._openai_client is not None:
            try:
                health_results["openai"] = await self._openai_client.health_check()
            except Exception as e:
                health_results["openai"] = {
                    "status": "unhealthy",
                    "provider": "openai",
                    "error": str(e),
                }

        if self._gemini_client is not None:
            try:
                health_results["gemini"] = await self._gemini_client.health_check()
            except Exception as e:
                health_results["gemini"] = {
                    "status": "unhealthy",
                    "provider": "gemini",
                    "error": str(e),
                }

        if self._azure_di_client is not None:
            try:
                health_results["azure_di"] = await self._azure_di_client.health_check()
            except Exception as e:
                health_results["azure_di"] = {
                    "status": "unhealthy",
                    "provider": "azure_di",
                    "error": str(e),
                }

        logger.info(
            "Health check complete",
            extra={"active_clients": len(health_results), "results": health_results},
        )

        return health_results

    async def cleanup(self):
        """
        Cleanup all active clients.

        Closes connections and releases resources for all initialized clients.
        Should be called on application shutdown.
        """
        logger.info("Cleaning up client factory")

        cleanup_count = 0

        if self._mistral_client is not None:
            # Mistral client doesn't need explicit cleanup
            self._mistral_client = None
            cleanup_count += 1

        if self._openai_client is not None:
            # OpenAI client doesn't need explicit cleanup
            self._openai_client = None
            cleanup_count += 1

        if self._gemini_client is not None:
            # Gemini client doesn't need explicit cleanup
            self._gemini_client = None
            cleanup_count += 1

        if self._azure_di_client is not None:
            # Azure DI client doesn't need explicit cleanup
            self._azure_di_client = None
            cleanup_count += 1

        logger.info(f"Cleaned up {cleanup_count} clients")

    def get_active_clients(self) -> list:
        """
        Get list of active (initialized) client names.

        Returns:
            list: Names of clients that have been initialized
        """
        active = []

        if self._mistral_client is not None:
            active.append("mistral")
        if self._openai_client is not None:
            active.append("openai")
        if self._gemini_client is not None:
            active.append("gemini")
        if self._azure_di_client is not None:
            active.append("azure_di")

        return active

    def reset(self):
        """
        Reset factory by clearing all clients.

        Useful for testing or forcing re-initialization.
        """
        logger.warning("Resetting client factory - all clients will be cleared")

        self._mistral_client = None
        self._openai_client = None
        self._gemini_client = None
        self._azure_di_client = None


# Global factory instance
_factory_instance: Optional[ClientFactory] = None


def get_client_factory() -> ClientFactory:
    """
    Get the global client factory instance (singleton).

    Returns:
        ClientFactory: The global factory instance

    Example:
        from src.services.client_factory import get_client_factory

        factory = get_client_factory()
        mistral = factory.mistral  # Lazy initialization
        health = await factory.health_check_all()
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = ClientFactory()

    return _factory_instance
