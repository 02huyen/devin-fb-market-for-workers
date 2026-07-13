import {
  API_URL,
  getImageUrl,
  requestLink,
  getListings,
  createListing,
  startConversation,
} from "@/lib/api";

describe("api client", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  function mockFetch(response: Partial<Response>) {
    const mock = jest.fn().mockResolvedValue(response as unknown as Response);
    (global as unknown as { fetch: typeof mock }).fetch = mock;
    return mock;
  }

  it("requestLink calls the backend with the email", async () => {
    const fetchMock = mockFetch({
      ok: true,
      json: async () => ({
        message: "Check your work email for a sign-in link.",
        dev_magic_link: "http://localhost:3000/verify?token=abc",
      }),
    });

    const result = await requestLink("test@example.com");

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/auth/request-link`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "test@example.com" }),
      })
    );
    expect(result.dev_magic_link).toBe("http://localhost:3000/verify?token=abc");
  });

  it("getListings builds the correct query string", async () => {
    const fetchMock = mockFetch({
      ok: true,
      json: async () => [],
    });

    await getListings({
      q: "bike",
      listing_type: "sell",
      status: "all",
      lat: 30.0,
      lng: -97.0,
      radius_miles: 10,
      seller_id: 5,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/listings?q=bike&listing_type=sell&status=all&lat=30&lng=-97&radius_miles=10&seller_id=5`,
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("createListing sends the payload as JSON", async () => {
    const fetchMock = mockFetch({
      ok: true,
      json: async () => ({ id: 1, title: "Bike" }),
    });

    await createListing({
      title: "Bike",
      description: "A bike",
      listing_type: "sell",
      price: 100,
      location_name: "Austin, TX",
      latitude: 30,
      longitude: -97,
      expiry_days: 7,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/listings`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          title: "Bike",
          description: "A bike",
          listing_type: "sell",
          price: 100,
          location_name: "Austin, TX",
          latitude: 30,
          longitude: -97,
          expiry_days: 7,
        }),
      })
    );
  });

  it("startConversation uses the listing_id query param", async () => {
    const fetchMock = mockFetch({
      ok: true,
      json: async () => ({ id: 3, listing_id: 7, other_participant: { id: 2, display_name: "Seller", company_name: "Example" } }),
    });

    const conv = await startConversation(7);

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/messages/conversations?listing_id=7`,
      expect.objectContaining({ method: "POST" })
    );
    expect(conv.id).toBe(3);
  });

  it("getImageUrl prepends the API URL for relative paths", () => {
    expect(getImageUrl("/uploads/photo.jpg")).toBe(`${API_URL}/uploads/photo.jpg`);
    expect(getImageUrl("https://cdn.example.com/photo.jpg")).toBe(
      "https://cdn.example.com/photo.jpg"
    );
  });

  it("throws on non-ok responses with the backend detail", async () => {
    mockFetch({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid expiry" }),
    });

    await expect(requestLink("test@example.com")).rejects.toThrow("Invalid expiry");
  });
});
