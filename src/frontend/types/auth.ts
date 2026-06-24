export interface TokenResponse {
  accessToken: string;
  tokenType: string;
  userId: string;
  username: string;
  displayName: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  displayName: string;
  isActive: boolean;
}
