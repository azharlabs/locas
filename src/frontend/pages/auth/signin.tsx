import { useEffect, useState } from 'react';
import { getProviders, signIn, useSession } from 'next-auth/react';
import { FaGoogle } from 'react-icons/fa';
import Layout from '../../components/Layout';
import axios from 'axios';
import { useRouter } from 'next/navigation'; // Import useRouter

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

const SignIn = () => {
  const [providers, setProviders] = useState<Record<string, any> | null>(null);
  const { data: session } = useSession();
  const [isSessionChecked, setIsSessionChecked] = useState(false);
  const router = useRouter(); // Use useRouter

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await getProviders();
        setProviders(response);
      } catch (error) {
        console.error("Error fetching providers:", error);
      }
    };

    fetchProviders();
  }, []);

  useEffect(() => {
    if (session) {
      router.push('/'); // Redirect to '/' if already logged in
    }
  }, [session, router]); // Add router to the dependency array

  useEffect(() => {
    const checkSession = async () => {
      if (session && !isSessionChecked) {
        try {
          // console.log("Sending user data to backend:", session.user);
          const response = await axios.post(`${API_URL}/api/user`, {
            id: session.user.id,
            name: session.user.name,
            email: session.user.email,
            image: session.user.image,
          });
          // console.log("Backend response:", response.data);
          setIsSessionChecked(true);
        } catch (error: any) {
          console.error('Error sending user data to backend:', error);
          if (error.response) {
            console.error("Backend error response:", error.response.data);
          }
        }
      }
    };

    checkSession();
  }, [session, isSessionChecked]);

  if (session) {
    // This return is now redundant because of the redirect in the useEffect
    return null; 
  }

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center min-h-screen py-2">
        <h1 className="text-4xl font-bold mb-6">Sign In</h1>
        {providers &&
          Object.values(providers).map((provider) => (
            <div key={provider.name}>
              <button
                onClick={() => signIn(provider.id)}
                className="flex items-center px-6 py-3 mt-4 rounded-md bg-gray-100 hover:bg-gray-200"
              >
                {provider.name === 'Google' && <FaGoogle className="mr-2" />}
                Sign in with {provider.name}
              </button>
            </div>
          ))}
      </div>
    </Layout>
  );
};

export default SignIn;
