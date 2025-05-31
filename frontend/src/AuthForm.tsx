import { useState, FormEvent } from "react";
import { useAuth } from "./AuthContext";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AuthForm() {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");

  const { signUp, signIn } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const { error } = isSignUp
        ? await signUp(email, password, name)
        : await signIn(email, password);

      if (error) {
        setMessage(error.message);
      } else if (isSignUp) {
        setMessage(
          "Compte créé ! Vérifiez votre email pour confirmer votre inscription."
        );
      }
    } catch {
      setMessage("Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#faf9f9] flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{isSignUp ? "Créer un compte" : "Se connecter"}</CardTitle>
          <CardDescription>
            {isSignUp
              ? "Entrez vos informations pour créer votre compte"
              : "Entrez votre email et mot de passe pour vous connecter"}
          </CardDescription>
          <CardAction>
            <Button
              variant="link"
              onClick={() => setIsSignUp(!isSignUp)}
              type="button"
            >
              {isSignUp ? "Se connecter" : "Créer un compte"}
            </Button>
          </CardAction>
        </CardHeader>

        <CardContent>
          {message && (
            <div
              className={`p-3 rounded mb-4 text-sm text-center ${
                message.includes("Compte créé") || message.includes("Vérifiez")
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              {isSignUp && (
                <div className="grid gap-2">
                  <Label htmlFor="name">Nom complet</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Votre nom complet"
                    value={name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setName(e.target.value)
                    }
                    required={isSignUp}
                  />
                </div>
              )}

              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="votre@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="grid gap-2">
                <div className="flex items-center">
                  <Label htmlFor="password">Mot de passe</Label>
                  {!isSignUp && (
                    <a
                      href="#"
                      className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                    >
                      Mot de passe oublié ?
                    </a>
                  )}
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
            </div>

            <CardFooter className="flex-col gap-2 mt-6">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading
                  ? "Chargement..."
                  : isSignUp
                  ? "Créer le compte"
                  : "Se connecter"}
              </Button>

              <Button variant="outline" className="w-full" type="button">
                {isSignUp
                  ? "S'inscrire avec Google"
                  : "Se connecter avec Google"}
              </Button>
            </CardFooter>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
