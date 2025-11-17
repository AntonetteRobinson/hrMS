import java.util.Scanner;

public class Mileage{
    /**Testing 1,2,3 */
    public static void main(String[] args){
        int miles;
        double gallons, mpg;
        Scanner s = new Scanner(System.in);

        System.out.println("Enter miles and gallons: ");
        miles = s.nextInt();
        gallons = s.nextDouble();
        mpg = miles / gallons;

        System.out.println("Miles" + "per" + "Gallon:" + mpg);
        System.out.println("hello world");
    }
}
