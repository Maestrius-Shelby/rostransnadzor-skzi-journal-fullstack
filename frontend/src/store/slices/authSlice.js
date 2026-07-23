import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import {
  loginRequest,
  refreshTokenRequest,
  logoutRequest,
} from "../../api/apiServices";
import { jwtDecode } from "jwt-decode";

const initialState = {
  user: null,
  authTokens: localStorage.getItem("authTokens")
    ? JSON.parse(localStorage.getItem("authTokens"))
    : null,
  loading: false,
  isAuthenticated: !!localStorage.getItem("authTokens"),
};

export const loginUser = createAsyncThunk(
  "auth/login",
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const data = await loginRequest(username, password);
      localStorage.setItem("authTokens", JSON.stringify(data));
      return data;
    } catch (err) {
      return rejectWithValue(err?.detail || "Ошибка входа");
    }
  },
);

export const refreshToken = createAsyncThunk(
  "auth/refresh",
  async (_, { getState, rejectWithValue }) => {
    try {
      const refresh = getState().auth.authTokens?.refresh;
      if (!refresh) return rejectWithValue("Нет refresh токена");
      const data = await refreshTokenRequest(refresh);
      localStorage.setItem("authTokens", JSON.stringify(data));
      return data;
    } catch {
      localStorage.removeItem("authTokens");
      return rejectWithValue("Сессия истекла");
    }
  },
);

export const logoutUser = createAsyncThunk("auth/logout", async () => {
  try {
    await logoutRequest();
  } catch {
    // Игнорируем ошибку при выходе
  }
  localStorage.removeItem("authTokens");
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuthTokens(state, action) {
      state.authTokens = action.payload;
      state.user = jwtDecode(action.payload.access_token);
      state.isAuthenticated = true;
    },
    removeAuthTokens(state) {
      state.authTokens = null;
      state.user = null;
      state.isAuthenticated = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.authTokens = action.payload;
        state.user = jwtDecode(action.payload.access_token);
        state.isAuthenticated = true;
        state.loading = false;
      })
      .addCase(loginUser.rejected, (state) => {
        state.loading = false;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.authTokens = action.payload;
        state.user = jwtDecode(action.payload.access_token);
        state.isAuthenticated = true;
      })
      .addCase(refreshToken.rejected, (state) => {
        state.authTokens = null;
        state.user = null;
        state.isAuthenticated = false;
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.authTokens = null;
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { setAuthTokens, removeAuthTokens } = authSlice.actions;
export default authSlice.reducer;
