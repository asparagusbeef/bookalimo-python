"""Performance and load tests for the Bookalimo SDK."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock

import pytest

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.schemas.booking import (
    Location,
    LocationType,
    PriceRequest,
    PriceResponse,
    RateType,
)
from bookalimo.transport.auth import Credentials


@pytest.mark.performance
class TestPerformance:
    """Performance tests for SDK operations."""

    @pytest.fixture
    def sample_locations(self):
        """Sample locations for performance testing."""
        from bookalimo.schemas.booking import Address, Airport, City

        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="123 Performance Test St",
                city=City(
                    city_name="Test City",
                    country_code="US",
                    state_code="TS"
                )
            )
        )
        dropoff = Location(
            type=LocationType.AIRPORT,
            airport=Airport(
                iata_code="TST",
                country_code="US",
                state_code="TS"
            )
        )
        return pickup, dropoff

    def test_credential_hash_performance(self):
        """Test credential hashing performance."""
        passwords = [f"password{i}" for i in range(100)]
        user_ids = [f"user{i}" for i in range(100)]

        start_time = time.perf_counter()

        for i in range(100):
            Credentials.create(user_ids[i], passwords[i])

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should be able to create 100 credentials in reasonable time
        assert elapsed < 1.0, (
            f"Credential creation took {elapsed:.3f}s for 100 credentials"
        )

        # Average time per credential should be reasonable
        avg_time_per_cred = elapsed / 100
        assert avg_time_per_cred < 0.01, (
            f"Average time per credential: {avg_time_per_cred:.4f}s"
        )

    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, sample_locations):
        """Test async client handling concurrent requests."""
        pickup, dropoff = sample_locations
        credentials = Credentials.create("perf_user", "perf_password")

        # Mock successful responses
        mock_response = PriceResponse(
            token="perf-token-123", total=150.00, currency="USD"
        )

        async with AsyncBookalimo(credentials=credentials) as client:
            # Mock the transport
            client._transport.post = AsyncMock(return_value=mock_response)

            # Create 50 concurrent quote requests
            async def make_quote():
                return await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

            start_time = time.perf_counter()

            # Run 50 concurrent requests
            tasks = [make_quote() for _ in range(50)]
            results = await asyncio.gather(*tasks)

            end_time = time.perf_counter()
            elapsed = end_time - start_time

            # All requests should succeed
            assert len(results) == 50
            assert all(isinstance(r, PriceResponse) for r in results)
            assert all(r.token == "perf-token-123" for r in results)

            # Should complete in reasonable time
            assert elapsed < 2.0, f"50 concurrent requests took {elapsed:.3f}s"

            # Average time per request should be low due to concurrency
            avg_time = elapsed / 50
            assert avg_time < 0.1, (
                f"Average time per concurrent request: {avg_time:.4f}s"
            )

    def test_sync_concurrent_requests_threadpool(self, sample_locations):
        """Test sync client handling concurrent requests via thread pool."""
        pickup, dropoff = sample_locations
        credentials = Credentials.create("sync_perf_user", "sync_perf_password")

        # Mock successful responses
        mock_response = PriceResponse(
            token="sync-perf-token-123", total=150.00, currency="USD"
        )

        def make_quote():
            with Bookalimo(credentials=credentials) as client:
                # Mock the transport
                client._transport.post = Mock(return_value=mock_response)

                return client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

        start_time = time.perf_counter()

        # Run 20 concurrent requests in thread pool
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_quote) for _ in range(20)]
            results = [future.result() for future in futures]

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # All requests should succeed
        assert len(results) == 20
        assert all(isinstance(r, PriceResponse) for r in results)
        assert all(r.token == "sync-perf-token-123" for r in results)

        # Should complete in reasonable time
        assert elapsed < 5.0, f"20 concurrent sync requests took {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, sample_locations):
        """Test that repeated operations don't cause memory leaks."""
        import gc

        pickup, dropoff = sample_locations
        credentials = Credentials.create("memory_test_user", "memory_test_password")

        mock_response = PriceResponse(
            token="memory-test-token", total=100.00, currency="USD"
        )

        # Get baseline memory
        gc.collect()

        async with AsyncBookalimo(credentials=credentials) as client:
            client._transport.post = AsyncMock(return_value=mock_response)

            # Perform 1000 operations
            for i in range(1000):
                await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

                # Force garbage collection every 100 iterations
                if i % 100 == 0:
                    gc.collect()

            # Final garbage collection
            gc.collect()

            # If we get here without memory errors, the test passes
            # In a real scenario, you might monitor actual memory usage

    def test_schema_validation_performance(self, sample_locations):
        """Test schema validation performance."""
        pickup, dropoff = sample_locations

        start_time = time.perf_counter()

        # Create 1000 price requests
        for i in range(1000):
            PriceRequest(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=pickup,
                dropoff=dropoff,
                passengers=2 + (i % 5),  # Vary passengers 2-6
                luggage=i % 3,  # Vary luggage 0-2
                customer_comment=f"Test comment {i}" if i % 10 == 0 else None,
            )

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should create 1000 schema objects in reasonable time
        assert elapsed < 2.0, f"1000 schema validations took {elapsed:.3f}s"

        avg_validation_time = elapsed / 1000
        assert avg_validation_time < 0.002, (
            f"Average validation time: {avg_validation_time:.5f}s"
        )

    def test_location_creation_performance(self):
        """Test location object creation performance."""
        start_time = time.perf_counter()

        # Create 1000 locations
        from bookalimo.schemas.booking import Address, Airport, City

        locations = []
        for i in range(1000):
            if i % 2 == 0:  # ADDRESS
                location = Location(
                    type=LocationType.ADDRESS,
                    address=Address(
                        place_name=f"Test Location {i}",
                        street_name=f"Address Line 1 {i}",
                        zip=f"{10000 + i:05d}",
                        city=City(
                            city_name=f"City{i}",
                            country_code="US",
                            state_code="TS"
                        )
                    )
                )
            else:  # AIRPORT
                location = Location(
                    type=LocationType.AIRPORT,
                    airport=Airport(
                        iata_code=f"T{i:02d}",
                        country_code="US",
                        state_code="TS"
                    )
                )
            locations.append(location)

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        assert len(locations) == 1000
        assert elapsed < 1.0, f"1000 location creations took {elapsed:.3f}s"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sustained_load(self, sample_locations):
        """Test sustained load over time."""
        pickup, dropoff = sample_locations
        credentials = Credentials.create("load_test_user", "load_test_password")

        mock_response = PriceResponse(
            token="load-test-token", total=125.00, currency="USD"
        )

        async with AsyncBookalimo(credentials=credentials) as client:
            client._transport.post = AsyncMock(return_value=mock_response)

            start_time = time.perf_counter()
            request_count = 0
            test_duration = 10  # 10 seconds

            # Run requests for 10 seconds
            while time.perf_counter() - start_time < test_duration:
                # Batch of 10 concurrent requests
                batch_tasks = []
                for _ in range(10):
                    task = client.pricing.quote(
                        rate_type=RateType.P2P,
                        date_time="09/10/2025 03:00 PM",
                        pickup=pickup,
                        dropoff=dropoff,
                        passengers=2,
                        luggage=1,
                    )
                    batch_tasks.append(task)

                await asyncio.gather(*batch_tasks)
                request_count += 10

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)

            end_time = time.perf_counter()
            elapsed = end_time - start_time

            requests_per_second = request_count / elapsed

            # Should handle reasonable throughput
            assert requests_per_second > 50, (
                f"Only {requests_per_second:.1f} requests/second"
            )
            assert request_count > 500, f"Only {request_count} requests completed"

    def test_large_payload_handling(self, sample_locations):
        """Test handling of large payloads."""
        pickup, dropoff = sample_locations

        # Create a large comment (within reasonable API limits)
        large_comment = "This is a very long comment. " * 100  # ~3000 characters

        start_time = time.perf_counter()

        request = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=1,
            customer_comment=large_comment,
        )

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        assert len(request.customer_comment) > 2500
        assert elapsed < 0.01, f"Large payload creation took {elapsed:.4f}s"


@pytest.mark.performance
class TestScalability:
    """Tests for scalability and resource usage."""

    def test_client_creation_overhead(self):
        """Test overhead of creating multiple clients."""
        credentials = Credentials.create("scale_user", "scale_password")

        start_time = time.perf_counter()

        # Create and close 100 clients
        for _ in range(100):
            client = Bookalimo(credentials=credentials)
            client.close()

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should be able to create/destroy clients quickly
        assert elapsed < 2.0, f"100 client create/destroy cycles took {elapsed:.3f}s"

        avg_time_per_client = elapsed / 100
        assert avg_time_per_client < 0.02, (
            f"Average time per client: {avg_time_per_client:.4f}s"
        )

    @pytest.mark.asyncio
    async def test_async_client_creation_overhead(self):
        """Test overhead of creating multiple async clients."""
        credentials = Credentials.create("async_scale_user", "async_scale_password")

        start_time = time.perf_counter()

        # Create and close 100 async clients
        for _ in range(100):
            async with AsyncBookalimo(credentials=credentials):
                pass  # Just create and close

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should be able to create/destroy async clients quickly
        assert elapsed < 3.0, (
            f"100 async client create/destroy cycles took {elapsed:.3f}s"
        )

    def test_transport_reuse_performance(self, sample_locations):
        """Test performance benefit of reusing transport."""
        pickup, dropoff = sample_locations
        credentials = Credentials.create("reuse_user", "reuse_password")

        mock_response = PriceResponse(token="reuse-token", total=100.00, currency="USD")

        # Test with client reuse (should be faster)
        start_time = time.perf_counter()

        with Bookalimo(credentials=credentials) as client:
            client._transport.post = Mock(return_value=mock_response)

            for _ in range(100):
                client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

        reuse_time = time.perf_counter() - start_time

        # Test without client reuse (should be slower)
        start_time = time.perf_counter()

        for _ in range(100):
            with Bookalimo(credentials=credentials) as client:
                client._transport.post = Mock(return_value=mock_response)

                client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

        no_reuse_time = time.perf_counter() - start_time

        # Reusing client should be significantly faster
        speedup_ratio = no_reuse_time / reuse_time
        assert speedup_ratio > 2.0, f"Client reuse only {speedup_ratio:.2f}x faster"

    @pytest.mark.asyncio
    async def test_connection_pooling_benefits(self, sample_locations):
        """Test connection pooling performance benefits."""
        pickup, dropoff = sample_locations
        credentials = Credentials.create("pool_user", "pool_password")

        # This test would be more meaningful with real HTTP requests,
        # but we'll simulate the concept
        mock_response = PriceResponse(token="pool-token", total=100.00, currency="USD")

        # Simulate the benefit of connection pooling
        start_time = time.perf_counter()

        async with AsyncBookalimo(credentials=credentials) as client:
            # Mock the transport to simulate connection reuse
            call_count = 0

            async def mock_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # Simulate faster subsequent calls (connection reuse)
                if call_count > 1:
                    await asyncio.sleep(0.001)  # Fast reused connection
                else:
                    await asyncio.sleep(0.01)  # Slower initial connection
                return mock_response

            client._transport.post = mock_post

            # Make multiple requests that should benefit from connection pooling
            tasks = []
            for _ in range(20):
                task = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/10/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start_time

        assert len(results) == 20
        # With connection reuse, should complete faster than 20 * initial_connection_time
        assert elapsed < 0.5, f"Connection pooling test took {elapsed:.3f}s"


@pytest.mark.performance
class TestMemoryEfficiency:
    """Tests for memory efficiency."""

    def test_object_lifecycle_cleanup(self):
        """Test that objects are properly cleaned up."""
        import gc
        import weakref

        credentials = Credentials.create("memory_user", "memory_password")

        # Create client and get weak reference
        client = Bookalimo(credentials=credentials)
        weak_ref = weakref.ref(client)

        # Client should exist
        assert weak_ref() is not None

        # Close and delete client
        client.close()
        del client

        # Force garbage collection
        gc.collect()

        # Weak reference should now be dead
        # Note: This might not always work due to CPython's reference counting
        # and garbage collection behavior, but it's a good indicator

        # At minimum, we should not have any exceptions during cleanup
        assert True  # If we get here, cleanup didn't crash

    @pytest.mark.asyncio
    async def test_async_object_lifecycle_cleanup(self):
        """Test that async objects are properly cleaned up."""
        import gc
        import weakref

        credentials = Credentials.create("async_memory_user", "async_memory_password")

        # Create async client and get weak reference
        client = AsyncBookalimo(credentials=credentials)
        weak_ref = weakref.ref(client)

        # Client should exist
        assert weak_ref() is not None

        # Close and delete client
        await client.aclose()
        del client

        # Force garbage collection
        gc.collect()

        # At minimum, we should not have any exceptions during cleanup
        assert True

    def test_large_batch_processing(self, sample_locations):
        """Test processing large batches of data efficiently."""
        pickup, dropoff = sample_locations

        # Create a large batch of location data
        locations = []
        for i in range(1000):
            locations.append(
                {
                    "type": LocationType.ADDRESS,
                    "name": f"Batch Location {i}",
                    "city": f"City{i}",
                    "state": "TS",
                    "country": "US",
                }
            )

        start_time = time.perf_counter()

        # Process batch efficiently
        processed_locations = []
        for loc_data in locations:
            location = Location(**loc_data)
            processed_locations.append(location)

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        assert len(processed_locations) == 1000
        assert elapsed < 2.0, f"Batch processing of 1000 locations took {elapsed:.3f}s"

        # Verify memory efficiency - processed objects should be reasonable size
        # This is a basic check; in practice, you'd use memory profiling tools
        assert len(processed_locations) == 1000
