import React from 'react';
import { signIn, signOut, useSession } from 'next-auth/react';
import { FaGoogle } from 'react-icons/fa';
import { useRouter } from 'next/navigation'; // Import useRouter

const LoginButton: React.FC = () => {
  const { data: session } = useSession();
  const router = useRouter(); // Use useRouter

  const handleSignIn = async () => {
    try {
      console.log("Signing in with Google from Navbar..."); // Log initiation
      // await signIn('google');
      // The following line is likely not needed, as signIn should redirect.
      router.push('/auth/signin'); 
    } catch (error) {
      console.error("Error during sign in:", error);
    }
  };

  if (session && session.user) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 rounded-full bg-white px-2 py-1 shadow-sm">
          {session.user.image ? (
            <div className="relative h-8 w-8 overflow-hidden rounded-full">
              <img
                src={session.user.image}
                alt={session.user.name || 'User'}
                className="h-full w-full object-cover"
              />
            </div>
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-800">
              {session.user.name?.charAt(0) || 'U'}
            </div>
          )}
          <span className="text-sm font-medium">{session.user.name}</span>
        </div>
        <button
          onClick={() => signOut()}
          className="btn btn-outline text-sm"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleSignIn} // Use handleSignIn
      className="btn btn-primary flex items-center gap-2"
    >
      <span>Sign in</span>
    </button>
  );
};

export default LoginButton;
